package main

import (
	"fmt"
	"io/ioutil"
	"log"
	"strings"
	"time"

	"github.com/gosnmp/gosnmp"
	"gopkg.in/yaml.v2"
)

// Profile represents the structure of a Datadog SNMP profile.
type Profile struct {
	Extends     []string `yaml:"extends"`
	SysObjectID string   `yaml:"sysobjectid"`
	Metadata    Metadata `yaml:"metadata"`
	Metrics     []Metric `yaml:"metrics"`
}

type Metadata struct {
	Device DeviceMetadata `yaml:"device"`
}

type DeviceMetadata struct {
	Fields map[string]Symbol `yaml:"fields"`
}

type Metric struct {
	MIB     string   `yaml:"MIB"`
	Symbol  *Symbol  `yaml:"symbol,omitempty"`
	Table   *Table   `yaml:"table,omitempty"`
	Symbols []Symbol `yaml:"symbols,omitempty"`
	Tags    []Tag    `yaml:"metric_tags,omitempty"`
}

type Symbol struct {
	OID          string `yaml:"OID"`
	Name         string `yaml:"name"`
	MatchPattern string `yaml:"match_pattern,omitempty"`
	MatchValue   string `yaml:"match_value,omitempty"`
}

type Table struct {
	OID  string `yaml:"OID"`
	Name string `yaml:"name"`
}

type Tag struct {
	Tag    string `yaml:"tag"`
	Symbol Symbol `yaml:"symbol"`
}

// Load YAML and merge profiles
func LoadYAML(filename string, basePath string) (*Profile, error) {
	data, err := ioutil.ReadFile(filename)
	if err != nil {
		return nil, err
	}

	var profile Profile
	err = yaml.Unmarshal(data, &profile)
	if err != nil {
		return nil, err
	}

	// If the profile extends other files, load and merge them
	for _, parentFile := range profile.Extends {
		parentProfile, err := LoadYAML(basePath+parentFile, basePath)
		if err != nil {
			return nil, err
		}
		MergeProfiles(&profile, parentProfile)
	}

	return &profile, nil
}

// Merge two profiles, giving priority to the child profile
func MergeProfiles(child, parent *Profile) {
	// Merge metadata
	for key, value := range parent.Metadata.Device.Fields {
		if _, exists := child.Metadata.Device.Fields[key]; !exists {
			child.Metadata.Device.Fields[key] = value
		}
	}

	// Merge metrics (append new ones)
	child.Metrics = append(parent.Metrics, child.Metrics...)
}

func main() {
	// Load profile
	profile, err := LoadYAML("fortinet-fortigate.yaml", "./profiles/")
	if err != nil {
		log.Fatalf("Failed to load profile: %v", err)
	}

	// Setup SNMP connection
	snmp := &gosnmp.GoSNMP{
		Target:    "20.20.21.1",
		Port:      161,
		Community: "public",
		Version:   gosnmp.Version2c,
		Timeout:   time.Duration(5) * time.Second,
		Retries:   3,
		// Logger:    log.New(os.Stdout, "", 0),
	}

	err = snmp.Connect()
	if err != nil {
		log.Fatalf("SNMP Connection failed: %v", err)
	}
	defer snmp.Conn.Close()

	fmt.Println("Starting SNMP Walk...")

	// Store unique results
	results := make(map[string]string)

	// Walk through the SNMP device
	for _, metric := range profile.Metrics {
		if metric.Symbol != nil {
			WalkOID(snmp, metric.Symbol.OID, metric.Symbol.Name, results)
		} else if metric.Table != nil {
			for _, sym := range metric.Symbols {
				WalkOID(snmp, sym.OID, sym.Name, results)
			}
		}
	}
}

func normalizeOID(oid string) string {
	parts := strings.Split(oid, ".")
	if len(parts) > 8 {
		// Keep the first 8 sections (e.g., .1.3.6.1.2.1.31.1.4.1) and ignore unique indexes
		return strings.Join(parts[:8], ".")
	}
	return oid
}

func WalkOID(snmp *gosnmp.GoSNMP, oid string, metricName string, results map[string]string) {
	err := snmp.Walk(oid, func(pdu gosnmp.SnmpPDU) error {
		rootOID, index := splitOID(pdu.Name)
		value := formatSNMPValue(pdu.Value)

		// Preserve tables with indexes while deduplicating non-indexed metrics
		if index != "" {
			// Indexed values should always be stored
			fullMetricName := fmt.Sprintf("%s[%s]", metricName, index)
			results[fullMetricName] = value
			fmt.Printf("%s (%s) = %s\n", fullMetricName, rootOID, value)
		} else {
			// Deduplicate only if the metric is repeated
			if existing, exists := results[rootOID]; !exists || existing != value {
				results[rootOID] = value
				fmt.Printf("%s (%s) = %s\n", metricName, rootOID, value)
			}
		}
		return nil
	})

	if err != nil {
		log.Printf("SNMP Walk failed for OID %s: %v", oid, err)
	}
}

func splitOID(oid string) (string, string) {
	parts := strings.Split(oid, ".")
	if len(parts) > 8 {
		rootOID := strings.Join(parts[:8], ".") // Keep the base OID
		index := strings.Join(parts[8:], ".")   // The rest is the unique index
		return rootOID, index
	}
	return oid, "" // Return full OID if no index
}

func getParentOID(oid string) string {
	lastDot := strings.LastIndex(oid, ".")
	if lastDot == -1 {
		return oid
	}
	return oid[:lastDot] // Remove last segment
}

// Format SNMP values
func formatSNMPValue(value interface{}) string {
	switch v := value.(type) {
	case []byte:
		return string(v) // Convert bytes to string
	case string:
		return v
	case uint, uint32, uint64, int, int32, int64, float32, float64:
		return fmt.Sprintf("%v", v)
	default:
		return fmt.Sprintf("Unsupported Type: %T", v)
	}
}
