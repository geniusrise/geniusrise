package gateway

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sync"
	"time"
)

type SpendEntry struct {
	NodeID       string     `json:"node_id"`
	Model        string     `json:"model"`
	PricePerHour float64    `json:"price_hr"`
	StartedAt    time.Time  `json:"started_at"`
	EndedAt      *time.Time `json:"ended_at,omitempty"`
}

type KeyUsage struct {
	Requests int64  `json:"requests"`
	Tokens   int64  `json:"tokens"`
	STTBytes int64  `json:"stt_bytes"`
	TTSChars int64  `json:"tts_chars"`
	Day      string `json:"day"`
	Month    string `json:"month"`
}

type State struct {
	mu           sync.Mutex
	Spend        []SpendEntry         `json:"spend"`
	Usage        map[string]*KeyUsage `json:"usage"`
	NodesSeen    map[string]bool      `json:"nodes_seen"`
	Alerts       []AlertRecord        `json:"alerts"`
	BudgetFrozen bool                 `json:"budget_frozen"`
	BudgetCapped bool                 `json:"budget_capped"`
	BudgetLevel  int                  `json:"budget_level"`
}

type AlertRecord struct {
	At      time.Time `json:"at"`
	Level   string    `json:"level"`
	Message string    `json:"message"`
}

func NewState() *State {
	return &State{Usage: map[string]*KeyUsage{}, NodesSeen: map[string]bool{}}
}

func LoadState(path string) (*State, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return NewState(), nil
		}
		return nil, err
	}
	var s State
	if err := json.Unmarshal(data, &s); err != nil {
		return nil, err
	}
	if s.Usage == nil {
		s.Usage = map[string]*KeyUsage{}
	}
	if s.NodesSeen == nil {
		s.NodesSeen = map[string]bool{}
	}
	return &s, nil
}

func (s *State) Save(path string) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.saveLocked(path)
}

func (s *State) saveLocked(path string) error {
	data, err := json.MarshalIndent(s, "", "  ")
	if err != nil {
		return err
	}
	tmp := path + ".tmp"
	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		return err
	}
	if err := os.WriteFile(tmp, data, 0o600); err != nil {
		return err
	}
	return os.Rename(tmp, path)
}

func (s *State) StartNode(id, model string, price float64) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.NodesSeen[id] = true
	for i := range s.Spend {
		if s.Spend[i].NodeID == id && s.Spend[i].EndedAt == nil {
			return
		}
	}
	s.Spend = append(s.Spend, SpendEntry{NodeID: id, Model: model, PricePerHour: price, StartedAt: time.Now().UTC()})
}

func (s *State) EndNode(id string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	now := time.Now().UTC()
	for i := range s.Spend {
		if s.Spend[i].NodeID == id && s.Spend[i].EndedAt == nil {
			s.Spend[i].EndedAt = &now
		}
	}
}

func (s *State) PruneNodes(known map[string]bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	now := time.Now().UTC()
	for i := range s.Spend {
		if s.Spend[i].EndedAt == nil && !known[s.Spend[i].NodeID] {
			s.Spend[i].EndedAt = &now
		}
	}
}

func (s *State) MonthSpend(now time.Time) float64 {
	s.mu.Lock()
	defer s.mu.Unlock()
	total := 0.0
	for _, e := range s.Spend {
		var end time.Time
		if e.EndedAt != nil {
			end = *e.EndedAt
		} else {
			end = now
		}
		if end.Before(time.Date(now.Year(), now.Month(), 1, 0, 0, 0, 0, time.UTC)) {
			continue
		}
		start := e.StartedAt
		if start.Before(time.Date(now.Year(), now.Month(), 1, 0, 0, 0, 0, time.UTC)) {
			start = time.Date(now.Year(), now.Month(), 1, 0, 0, 0, 0, time.UTC)
		}
		total += end.Sub(start).Hours() * e.PricePerHour
	}
	return total
}

func (s *State) usageFor(key string, now time.Time) *KeyUsage {
	u, ok := s.Usage[key]
	today := now.UTC().Format("2006-01-02")
	month := now.UTC().Format("2006-01")
	if !ok || u.Day != today || u.Month != month {
		u = &KeyUsage{Day: today, Month: month}
		s.Usage[key] = u
	}
	return u
}

func (s *State) RecordRequest(key string, tokens, sttBytes, ttsChars int64) {
	s.mu.Lock()
	defer s.mu.Unlock()
	now := time.Now().UTC()
	u := s.usageFor(key, now)
	u.Requests++
	u.Tokens += tokens
	u.STTBytes += sttBytes
	u.TTSChars += ttsChars
}

func (s *State) UsageFor(key string) KeyUsage {
	s.mu.Lock()
	defer s.mu.Unlock()
	u := s.usageFor(key, time.Now().UTC())
	return *u
}

func (s *State) AllUsage() map[string]KeyUsage {
	s.mu.Lock()
	defer s.mu.Unlock()
	out := map[string]KeyUsage{}
	for k, u := range s.Usage {
		out[k] = *u
	}
	return out
}

func (s *State) AddAlert(level, message string) AlertRecord {
	s.mu.Lock()
	defer s.mu.Unlock()
	rec := AlertRecord{At: time.Now().UTC(), Level: level, Message: message}
	s.Alerts = append(s.Alerts, rec)
	if len(s.Alerts) > 100 {
		s.Alerts = s.Alerts[len(s.Alerts)-100:]
	}
	return rec
}

func (s *State) SetBudget(level int, frozen, capped bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.BudgetLevel = level
	s.BudgetFrozen = frozen
	s.BudgetCapped = capped
}

func (s *State) BudgetState() (int, bool, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.BudgetLevel, s.BudgetFrozen, s.BudgetCapped
}

type alertPayload struct {
	Deployment string  `json:"deployment"`
	Level      string  `json:"level"`
	Message    string  `json:"message"`
	SpendUSD   float64 `json:"spend_usd"`
	BudgetUSD  float64 `json:"budget_usd"`
	At         string  `json:"at"`
}

func spendWithGateway(nodes float64, monthlyGateway float64, now time.Time) float64 {
	daysInMonth := time.Date(now.Year(), now.AddDate(0, 1, 0).Month(), 0, 0, 0, 0, 0, time.UTC).Day()
	day := now.UTC().Day()
	return nodes + monthlyGateway*float64(day)/float64(daysInMonth)
}
