package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/geniusrise/geniusrise/internal/pricing"
)

var hc = &http.Client{Timeout: 120 * time.Second}

func getJSON(url string, out any) error {
	resp, err := hc.Get(url)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("status %d for %s", resp.StatusCode, url)
	}
	return json.NewDecoder(resp.Body).Decode(out)
}

func fetchAzure() (map[string][]pricing.Offering, error) {
	type item struct {
		MeterID          string `json:"meterId"`
		MeterName        string `json:"meterName"`
		ProductName      string `json:"productName"`
		SkuName          string `json:"skuName"`
		MeterCategory    string `json:"meterCategory"`
		MeterSubCategory string `json:"meterSubCategory"`
		UnitPrice        float64 `json:"unitPrice"`
		UnitOfMeasure    string `json:"unitOfMeasure"`
		ArmRegionName    string `json:"armRegionName"`
		Type             string `json:"type"`
		ReservationTerm  string `json:"reservationTerm"`
	}
	var page struct {
		Items     []item `json:"Items"`
		NextPage  string `json:"NextPageLink"`
	}
	url := "https://prices.azure.com/api/retail/prices?$filter=" + strings.Join([]string{
		"serviceName eq 'Virtual Machines'",
		"priceType eq 'Consumption'",
	}, " and ")
	out := map[string][]pricing.Offering{}
	for url != "" {
		if err := getJSON(url, &page); err != nil {
			return nil, err
		}
		for _, it := range page.Items {
			o, ok := azureMapItem(it)
			if !ok {
				continue
			}
			out[it.ArmRegionName] = append(out[it.ArmRegionName], o)
		}
		url = page.NextPage
	}
	if len(out) == 0 {
		return nil, fmt.Errorf("no azure offerings parsed")
	}
	return out, nil
}

func azureMapItem(it struct {
	MeterID          string `json:"meterId"`
	MeterName        string `json:"meterName"`
	ProductName      string `json:"productName"`
	SkuName          string `json:"skuName"`
	MeterCategory    string `json:"meterCategory"`
	MeterSubCategory string `json:"meterSubCategory"`
	UnitPrice        float64 `json:"unitPrice"`
	UnitOfMeasure    string `json:"unitOfMeasure"`
	ArmRegionName    string `json:"armRegionName"`
	Type             string `json:"type"`
	ReservationTerm  string `json:"reservationTerm"`
}) (pricing.Offering, bool) {
	if it.UnitOfMeasure != "1 Hour" || strings.Contains(it.ProductName, "Windows") {
		return pricing.Offering{}, false
	}
	sku := it.MeterSubCategory
	if sku == "" {
		sku = it.ProductName
	}
	cap := pricing.CapacityOnDemand
	if strings.Contains(it.Type, "Spot") {
		cap = pricing.CapacitySpot
	}
	var gpu, typ string
	switch {
	case strings.HasPrefix(sku, "NC4as T4 v3"):
		gpu, typ = "T4", sku
	case strings.HasPrefix(sku, "NV36ads A10 v5"):
		gpu, typ = "A10G", sku
	case strings.HasPrefix(sku, "NC A100 v4"):
		gpu, typ = "A100-80", sku
	case strings.HasPrefix(sku, "ND A100 v4"):
		gpu, typ = "A100-40", sku
	case strings.HasPrefix(sku, "ND H100 v5"):
		gpu, typ = "H100", sku
	case sku == "D4s v5" || sku == "D4s v4":
		gpu, typ = "cpu", sku
	default:
		return pricing.Offering{}, false
	}
	if strings.Contains(it.MeterName, "Low Priority") || it.ReservationTerm != "" {
		return pricing.Offering{}, false
	}
	return pricing.Offering{GPUClass: gpu, InstanceType: typ, Capacity: cap, USDPerHour: it.UnitPrice, Available: true}, true
}

func fetchGCP() (map[string][]pricing.Offering, error) {
	key := os.Getenv("GCP_BILLING_API_KEY")
	if key == "" {
		return nil, fmt.Errorf("GCP_BILLING_API_KEY not set")
	}
	type sku struct {
		Description string `json:"description"`
		ServiceRegions []string `json:"serviceRegions"`
		PricingInfo []struct {
			PricingExpression struct {
				TieredRates []struct {
					UnitPrice struct {
						Units string `json:"units"`
						Nanos int64  `json:"nanos"`
					} `json:"unitPrice"`
				} `json:"tieredRates"`
			} `json:"pricingExpression"`
		} `json:"pricingInfo"`
		ResourceFamily string `json:"resourceFamily"`
	}
	var page struct {
		Skus     []sku   `json:"skus"`
		NextPageToken string `json:"nextPageToken"`
	}
	url := fmt.Sprintf("https://cloudbilling.googleapis.com/v1/services/6F81-5844-456A/skus?key=%s", key)
	out := map[string][]pricing.Offering{}
	for url != "" {
		if err := getJSON(url, &page); err != nil {
			return nil, err
		}
		for _, s := range page.Skus {
			o, ok := gcpMapSKU(s)
			if !ok {
				continue
			}
			for _, r := range s.ServiceRegions {
				out[r] = append(out[r], o)
			}
		}
		if page.NextPageToken == "" {
			break
		}
		url = fmt.Sprintf("https://cloudbilling.googleapis.com/v1/services/6F81-5844-456A/skus?key=%s&pageToken=%s", key, page.NextPageToken)
	}
	if len(out) == 0 {
		return nil, fmt.Errorf("no gcp offerings parsed")
	}
	return out, nil
}

func gcpMapSKU(s struct {
	Description string `json:"description"`
	ServiceRegions []string `json:"serviceRegions"`
	PricingInfo []struct {
		PricingExpression struct {
			TieredRates []struct {
				UnitPrice struct {
					Units string `json:"units"`
					Nanos int64  `json:"nanos"`
				} `json:"unitPrice"`
			} `json:"tieredRates"`
		} `json:"pricingExpression"`
	} `json:"pricingInfo"`
	ResourceFamily string `json:"resourceFamily"`
}) (pricing.Offering, bool) {
	if len(s.PricingInfo) == 0 || len(s.PricingInfo[0].PricingExpression.TieredRates) == 0 {
		return pricing.Offering{}, false
	}
	rate := s.PricingInfo[0].PricingExpression.TieredRates[0].UnitPrice
	var price float64
	fmt.Sscanf(rate.Units, "%f", &price)
	price += float64(rate.Nanos) / 1e9
	cap := pricing.CapacityOnDemand
	if strings.Contains(s.Description, "Spot") || strings.Contains(s.Description, "Preemptible") {
		cap = pricing.CapacitySpot
	}
	d := s.Description
	var gpu string
	switch {
	case strings.Contains(d, "NVIDIA Tesla T4"):
		gpu = "T4"
	case strings.Contains(d, "NVIDIA L4"):
		gpu = "L4"
	case strings.Contains(d, "NVIDIA A100 80GB"):
		gpu = "A100-80"
	case strings.Contains(d, "NVIDIA A100"):
		gpu = "A100-40"
	case strings.Contains(d, "NVIDIA H100"):
		gpu = "H100"
	case strings.Contains(d, "NVIDIA H200"):
		gpu = "H200"
	default:
		return pricing.Offering{}, false
	}
	return pricing.Offering{GPUClass: gpu, InstanceType: d, Capacity: cap, USDPerHour: price, Available: true}, true
}

func fetchRunPod() (map[string][]pricing.Offering, error) {
	key := os.Getenv("RUNPOD_API_KEY")
	if key == "" {
		return nil, fmt.Errorf("RUNPOD_API_KEY not set")
	}
	var resp struct {
		Data struct {
			GpuTypes []struct {
				ID            string  `json:"id"`
				DisplayName   string  `json:"displayName"`
				PricePerHour  float64 `json:"pricePerHour"`
				SpotPricePerHour float64 `json:"spotPricePerHour"`
				CommunityCloud bool   `json:"communityCloud"`
			} `json:"gpuTypes"`
		} `json:"data"`
	}
	body := `{"query":"{ gpuTypes { id displayName pricePerHour spotPricePerHour communityCloud } }"}`
	resp2, err := hc.Post("https://api.runpod.io/graphql?api_key="+key, "application/json", strings.NewReader(body))
	if err != nil {
		return nil, err
	}
	defer resp2.Body.Close()
	if err := json.NewDecoder(resp2.Body).Decode(&resp); err != nil {
		return nil, err
	}
	var offs []pricing.Offering
	for _, g := range resp.Data.GpuTypes {
		if g.CommunityCloud {
			continue
		}
		var gpu string
		id := g.DisplayName + " " + g.ID
		switch {
		case strings.Contains(id, "A30"):
			gpu = "T4"
		case strings.Contains(id, "A40"):
			gpu = "L4"
		case strings.Contains(id, "A100 PCIe"):
			gpu = "A100-40"
		case strings.Contains(id, "A100 SXM"):
			gpu = "A100-80"
		case strings.Contains(id, "H100"):
			gpu = "H100"
		default:
			continue
		}
		if g.PricePerHour > 0 {
			offs = append(offs, pricing.Offering{GPUClass: gpu, InstanceType: g.DisplayName, Capacity: pricing.CapacityOnDemand, USDPerHour: g.PricePerHour, Available: true})
		}
		if g.SpotPricePerHour > 0 {
			offs = append(offs, pricing.Offering{GPUClass: gpu, InstanceType: g.DisplayName, Capacity: pricing.CapacitySpot, USDPerHour: g.SpotPricePerHour, Available: true})
		}
	}
	if len(offs) == 0 {
		return nil, fmt.Errorf("no runpod offerings parsed")
	}
	return map[string][]pricing.Offering{"global": offs}, nil
}

func fetchLambda() (map[string][]pricing.Offering, error) {
	key := os.Getenv("LAMBDA_API_KEY")
	if key == "" {
		return nil, fmt.Errorf("LAMBDA_API_KEY not set")
	}
	req, _ := http.NewRequest("GET", "https://cloud.lambda.ai/api/v1/instance-types", nil)
	req.Header.Set("Authorization", "Bearer "+key)
	resp, err := hc.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	var data struct {
		Data []struct {
			Name string `json:"name"`
			Price struct {
				Amount string `json:"amount"`
			} `json:"price"`
		} `json:"data"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&data); err != nil {
		return nil, err
	}
	var offs []pricing.Offering
	for _, it := range data.Data {
		var gpu string
		switch {
		case strings.Contains(it.Name, "a10"):
			gpu = "A10G"
		case strings.Contains(it.Name, "a100_sxm"):
			gpu = "A100-40"
		case strings.Contains(it.Name, "a100_80"):
			gpu = "A100-80"
		case strings.Contains(it.Name, "h100"):
			gpu = "H100"
		case strings.Contains(it.Name, "h200"):
			gpu = "H200"
		default:
			continue
		}
		var price float64
		fmt.Sscanf(it.Price.Amount, "%f", &price)
		offs = append(offs, pricing.Offering{GPUClass: gpu, InstanceType: it.Name, Capacity: pricing.CapacityOnDemand, USDPerHour: price, Available: true})
	}
	if len(offs) == 0 {
		return nil, fmt.Errorf("no lambda offerings parsed")
	}
	return map[string][]pricing.Offering{"global": offs}, nil
}

func fetchHyperbolic() (map[string][]pricing.Offering, error) {
	key := os.Getenv("HYPERBOLIC_API_KEY")
	if key == "" {
		return nil, fmt.Errorf("HYPERBOLIC_API_KEY not set")
	}
	req, _ := http.NewRequest("GET", "https://api.hyperbolic.xyz/v1/marketplace/gpuavailability", nil)
	req.Header.Set("Authorization", "Bearer "+key)
	resp, err := hc.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	var data []struct {
		GPUType string `json:"gpu_type"`
		PricePerHour float64 `json:"price_per_hour"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&data); err != nil {
		return nil, err
	}
	var offs []pricing.Offering
	for _, it := range data {
		g := it.GPUType
		var gpu string
		switch {
		case strings.Contains(g, "a100-40"):
			gpu = "A100-40"
		case strings.Contains(g, "a100-80"):
			gpu = "A100-80"
		case strings.Contains(g, "h100"):
			gpu = "H100"
		case strings.Contains(g, "h200"):
			gpu = "H200"
		default:
			continue
		}
		offs = append(offs, pricing.Offering{GPUClass: gpu, InstanceType: g, Capacity: pricing.CapacityOnDemand, USDPerHour: it.PricePerHour, Available: true})
	}
	if len(offs) == 0 {
		return nil, fmt.Errorf("no hyperbolic offerings parsed")
	}
	return map[string][]pricing.Offering{"global": offs}, nil
}
