package main

import "encoding/json"

func jsonUnmarshal(b []byte, out any) error {
	return json.Unmarshal(b, out)
}
