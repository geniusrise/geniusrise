package main

import (
	"context"
	"fmt"
	"log"
	"strings"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	awsconfig "github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/ec2"
	ec2types "github.com/aws/aws-sdk-go-v2/service/ec2/types"
	awspricing "github.com/aws/aws-sdk-go-v2/service/pricing"
	awspricingtypes "github.com/aws/aws-sdk-go-v2/service/pricing/types"

	"github.com/geniusrise/geniusrise/internal/pricing"
)

var awsRegions = []string{"us-east-1", "us-west-2", "eu-central-1", "ap-south-1", "ap-southeast-1"}

var awsFamilies = map[string]string{
	"c7i":  "cpu",
	"g4dn": "T4",
	"g5":   "A10G",
	"g6":   "L4",
	"g6e":  "L40S",
	"p4d":  "A100-40",
	"p4de": "A100-80",
	"p5":   "H100",
}

func familyOf(instanceType string) (string, string) {
	parts := strings.SplitN(instanceType, ".", 2)
	if len(parts) != 2 {
		return "", ""
	}
	f := parts[0]
	gpu, ok := awsFamilies[f]
	return f, gpuMap(f, gpu, ok)
}

func gpuMap(f, gpu string, ok bool) string {
	if !ok {
		return ""
	}
	return gpu
}

func fetchAWS() (map[string][]pricing.Offering, error) {
	ctx := context.Background()
	cfg, err := awsconfig.LoadDefaultConfig(ctx, awsconfig.WithRegion("us-east-1"))
	if err != nil {
		return nil, err
	}
	pc := awspricing.NewFromConfig(cfg)
	var filters []awspricingtypes.Filter
	for _, loc := range []string{"US East (N. Virginia)", "US West (Oregon)", "EU (Frankfurt)", "Asia Pacific (Mumbai)", "Asia Pacific (Singapore)"} {
		filters = append(filters, awspricingtypes.Filter{Field: aws.String("location"), Type: "TERM_MATCH", Value: aws.String(loc)})
		break
	}
	_ = filters
	out := map[string][]pricing.Offering{}
	var next *string
	for {
		resp, err := pc.GetProducts(ctx, &awspricing.GetProductsInput{
			ServiceCode: aws.String("AmazonEC2"),
			NextToken:   next,
			Filters: []awspricingtypes.Filter{
				{Field: aws.String("preInstalledSw"), Type: "TERM_MATCH", Value: aws.String("NA")},
				{Field: aws.String("operatingSystem"), Type: "TERM_MATCH", Value: aws.String("Linux")},
				{Field: aws.String("capacitystatus"), Type: "TERM_MATCH", Value: aws.String("Used")},
				{Field: aws.String("tenancy"), Type: "TERM_MATCH", Value: aws.String("Shared")},
			},
			MaxResults: aws.Int32(100),
		})
		if err != nil {
			return nil, err
		}
		for _, priceStr := range resp.PriceList {
			var p awsProduct
			decodeProduct(priceStr, &p)
			if p.Product.Attributes.Location == "" || !strings.HasSuffix(p.Product.Attributes.OperatingSystem, "Linux") {
				continue
			}
			_, gpu := familyOf(p.Product.Attributes.InstanceType)
			if gpu == "" {
				continue
			}
			region := locationToRegion(p.Product.Attributes.Location)
			if region == "" {
				continue
			}
			onDemand, spot := p.rates()
			if onDemand > 0 {
				out[region] = append(out[region], pricing.Offering{GPUClass: gpu, InstanceType: p.Product.Attributes.InstanceType, Capacity: pricing.CapacityOnDemand, USDPerHour: onDemand, Available: true})
			}
			if spot > 0 {
				out[region] = append(out[region], pricing.Offering{GPUClass: gpu, InstanceType: p.Product.Attributes.InstanceType, Capacity: pricing.CapacitySpot, USDPerHour: spot, Available: true})
			}
		}
		if resp.NextToken == nil {
			break
		}
		next = resp.NextToken
	}
	addSpotPrices(ctx, out)
	if len(out) == 0 {
		return nil, fmt.Errorf("no aws offerings parsed")
	}
	return out, nil
}

func addSpotPrices(ctx context.Context, out map[string][]pricing.Offering) {
	cfg, err := awsconfig.LoadDefaultConfig(ctx, awsconfig.WithRegion("us-east-1"))
	if err != nil {
		log.Println("spot prices:", err)
		return
	}
	for _, region := range awsRegions {
		if len(out[region]) == 0 {
			continue
		}
		rcfg := awsconfig.WithRegion(region)
		rc, err := awsconfig.LoadDefaultConfig(ctx, rcfg)
		if err != nil {
			continue
		}
		ec := ec2.NewFromConfig(rc)
		start := time.Now().Add(-3 * 24 * time.Hour)
		var types []string
		seen := map[string]bool{}
		for _, o := range out[region] {
			if o.Capacity == pricing.CapacityOnDemand && !seen[o.InstanceType] {
				seen[o.InstanceType] = true
				types = append(types, o.InstanceType)
			}
		}
		for i := 0; i < len(types); i += 50 {
			chunk := types[i:min(i+50, len(types))]
			resp, err := ec.DescribeSpotPriceHistory(ctx, &ec2.DescribeSpotPriceHistoryInput{
				StartTime:           &start,
				InstanceTypes:       strSliceToEc2Types(chunk),
				ProductDescriptions: []string{"Linux/UNIX"},
			}, func(o *ec2.Options) { o.Region = region })
			if err != nil {
				continue
			}
			lowest := map[string]float64{}
			for _, sp := range resp.SpotPriceHistory {
				var price float64
				fmt.Sscanf(aws.ToString(sp.SpotPrice), "%f", &price)
				it := string(sp.InstanceType)
				if v, ok := lowest[it]; !ok || price < v {
					lowest[it] = price
				}
			}
			for it, price := range lowest {
				for i, o := range out[region] {
					if o.InstanceType == it && o.Capacity == pricing.CapacitySpot {
						out[region][i].USDPerHour = price
						out[region][i].Available = true
					}
				}
			}
		}
		_ = cfg
	}
}

func strSliceToEc2Types(in []string) []ec2types.InstanceType {
	var out []ec2types.InstanceType
	for _, s := range in {
		out = append(out, ec2types.InstanceType(s))
	}
	return out
}

func locationToRegion(loc string) string {
	switch loc {
	case "US East (N. Virginia)", "US East (Ohio)":
		return "us-east-1"
	case "US West (Oregon)":
		return "us-west-2"
	case "EU (Frankfurt)":
		return "eu-central-1"
	case "Asia Pacific (Mumbai)":
		return "ap-south-1"
	case "Asia Pacific (Singapore)":
		return "ap-southeast-1"
	}
	return ""
}

type awsProduct struct {
	Product struct {
		Attributes struct {
			Location        string `json:"location"`
			InstanceType    string `json:"instanceType"`
			OperatingSystem string `json:"operatingSystem"`
		} `json:"attributes"`
	} `json:"product"`
	Terms struct {
		OnDemand map[string]struct {
			PriceDimensions map[string]struct {
				PricePerUnit struct {
					USD string `json:"USD"`
				} `json:"pricePerUnit"`
			} `json:"priceDimensions"`
		} `json:"OnDemand"`
		Reserved map[string]struct {
			PriceDimensions map[string]struct {
				PricePerUnit struct {
					USD string `json:"USD"`
				} `json:"pricePerUnit"`
			} `json:"priceDimensions"`
		} `json:"Reserved"`
	} `json:"terms"`
}

func (p awsProduct) rates() (onDemand, spot float64) {
	for _, t := range p.Terms.OnDemand {
		for _, d := range t.PriceDimensions {
			fmt.Sscanf(d.PricePerUnit.USD, "%f", &onDemand)
		}
	}
	return onDemand, 0
}

func decodeProduct(s string, out *awsProduct) {
	b := []byte(s)
	_ = jsonUnmarshal(b, out)
}
