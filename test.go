package main

import (
	"bytes"
	"fmt"
	"io/ioutil"
	"log"
	"net"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/gosnmp/gosnmp"
	"gopkg.in/yaml.v2"
)

// Profile represents the structure of a Datadog SNMP profile.
type Profile struct {
	Extends     []string     `yaml:"extends"`
	SysObjectID SysObjectIDs `yaml:"sysobjectid"`
	Metadata    Metadata     `yaml:"metadata"`
	Metrics     []Metric     `yaml:"metrics"`
}

// SysObjectIDs allows both a string and list of strings for sysobjectid.
type SysObjectIDs []string

func (s *SysObjectIDs) UnmarshalYAML(unmarshal func(interface{}) error) error {
	var single string
	if err := unmarshal(&single); err == nil {
		*s = []string{single}
		return nil
	}

	var multiple []string
	if err := unmarshal(&multiple); err == nil {
		*s = multiple
		return nil
	}

	return fmt.Errorf("invalid sysobjectid format")
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

// Load all profiles from the directory
func LoadAllProfiles(profileDir string) (map[string]*Profile, error) {
	profiles := make(map[string]*Profile)

	err := filepath.Walk(profileDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if strings.HasSuffix(info.Name(), ".yaml") {
			profile, err := LoadYAML(path, profileDir)
			if err == nil {
				profiles[path] = profile
			} else {
				log.Printf("Skipping invalid YAML: %s (%v)\n", path, err)
			}
		}
		return nil
	})

	if err != nil {
		return nil, err
	}

	return profiles, nil
}

// Load a single YAML profile
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
		parentProfile, err := LoadYAML(filepath.Join(basePath, parentFile), basePath)
		if err != nil {
			return nil, err
		}
		MergeProfiles(&profile, parentProfile)
	}

	return &profile, nil
}

// Merge two profiles, giving priority to the child profile
func MergeProfiles(child, parent *Profile) {
	// Initialize child metadata fields if nil
	if child.Metadata.Device.Fields == nil {
		child.Metadata.Device.Fields = make(map[string]Symbol)
	}

	// Merge metadata
	for key, value := range parent.Metadata.Device.Fields {
		if _, exists := child.Metadata.Device.Fields[key]; !exists {
			child.Metadata.Device.Fields[key] = value
		}
	}

	// Merge metrics (append new ones)
	child.Metrics = append(parent.Metrics, child.Metrics...)
}

// Find the matching profile based on sysObjectID
func FindMatchingProfiles(profiles map[string]*Profile, deviceOID string) []*Profile {
	var matchedProfiles []*Profile

	for _, profile := range profiles {
		for _, oidPattern := range profile.SysObjectID {
			if strings.HasPrefix(deviceOID, strings.Split(oidPattern, "*")[0]) {
				matchedProfiles = append(matchedProfiles, profile)
				break
			}
		}
	}

	return matchedProfiles
}

// Discover all SNMP-enabled devices in the subnet
func ScanSubnet(subnet string, community string, timeout time.Duration) []string {
	ips := []string{}
	ip, ipNet, err := net.ParseCIDR(subnet)
	if err != nil {
		log.Fatalf("Invalid subnet format: %v", err)
	}

	var wg sync.WaitGroup
	ipMutex := &sync.Mutex{}

	for ip := ip.Mask(ipNet.Mask); ipNet.Contains(ip); inc(ip) {
		targetIP := ip.String()
		wg.Add(1)

		go func(ip string) {
			defer wg.Done()
			if isSNMPDevice(ip, community, timeout) {
				ipMutex.Lock()
				ips = append(ips, ip)
				ipMutex.Unlock()
				fmt.Printf("SNMP Device Found: %s\n", ip)
			}
		}(targetIP)
	}

	wg.Wait()
	return ips
}

// Check if an IP is an SNMP-enabled device
func isSNMPDevice(ip, community string, timeout time.Duration) bool {
	snmp := &gosnmp.GoSNMP{
		Target:    ip,
		Port:      161,
		Community: community,
		Version:   gosnmp.Version2c,
		Timeout:   timeout,
		Retries:   1,
	}

	err := snmp.Connect()
	if err != nil {
		return false
	}
	defer snmp.Conn.Close()

	// Check sysObjectID to verify SNMP response
	oid := "1.3.6.1.2.1.1.2.0" // sysObjectID
	result, err := snmp.Get([]string{oid})
	if err != nil || len(result.Variables) == 0 {
		return false
	}
	return true
}

// Increment IP address
func inc(ip net.IP) {
	for j := len(ip) - 1; j >= 0; j-- {
		ip[j]++
		if ip[j] > 0 {
			break
		}
	}
}

// Get sysObjectID dynamically from SNMP
func GetSysObjectID(snmp *gosnmp.GoSNMP) (string, error) {
	oid := "1.3.6.1.2.1.1.2.0" // Standard sysObjectID OID
	result, err := snmp.Get([]string{oid})
	if err != nil {
		return "", err
	}

	if len(result.Variables) == 0 {
		return "", fmt.Errorf("no sysObjectID found")
	}

	return strings.SplitN(fmt.Sprintf("%v", result.Variables[0].Value), ".", 2)[1], nil
}

// Execute SNMPWalk via shell command
func SNMPWalkExec(target string, community string) (map[string]string, error) {
	results := make(map[string]string)

	fmt.Printf("Executing SNMP walk for device %s\n", target)

	// Construct the snmpwalk command
	cmd := exec.Command("snmpwalk", "-v2c", "-c", community, target, "1.3.6.1.4.1") // Walk entire SNMP tree

	// Capture the output
	var out bytes.Buffer
	cmd.Stdout = &out

	// Run the command
	err := cmd.Run()
	if err != nil {
		return nil, fmt.Errorf("snmpwalk failed: %v", err)
	}

	fmt.Print("Command ran\nParsing output\n")

	// Parse output
	lines := strings.Split(out.String(), "\n")
	for _, line := range lines {
		parts := strings.SplitN(line, " = ", 2)
		if len(parts) == 2 {
			oid := strings.Replace(strings.TrimSpace(parts[0]), "iso", "1", -1)
			value := strings.TrimSpace(parts[1])
			results[oid] = value
		}
	}

	fmt.Print("Parsing done\n")

	return results, nil
}

// Execute SNMPWalk via shell command
func SNMPGetExec(target string, oid string, community string) (string, error) {
	// result := make(map[string]string)

	// Construct the snmpwalk command
	cmd := exec.Command("snmpget", "-v2c", "-c", community, target, oid) // Walk entire SNMP tree

	// Capture the output
	var out bytes.Buffer
	cmd.Stdout = &out

	// Run the command
	err := cmd.Run()
	if err != nil {
		return "error", fmt.Errorf("snmpget failed: %v", err)
	}

	// // Parse output
	// lines := strings.Split(out.String(), "\n")
	// for _, line := range lines {
	// 	parts := strings.SplitN(line, " = ", 2)
	// 	if len(parts) == 2 {
	// 		oid := strings.Replace(strings.TrimSpace(parts[0]), "iso", "1", -1)
	// 		value := strings.TrimSpace(parts[1])
	// 		results[oid] = value
	// 	}
	// }
	return out.String(), nil

}

func main() {
	profileDir := "./default_profiles/"
	// profileDir := "./integrations-core/snmp/datadog_checks/snmp/data/default_profiles/"
	subnet := "20.20.21.0/24" // CHANGE THIS TO YOUR SUBNET
	community := "public"
	timeout := 2 * time.Second

	// Load all profiles
	profiles, err := LoadAllProfiles(profileDir)
	if err != nil {
		log.Fatalf("Failed to load profiles: %v", err)
	}

	devices := ScanSubnet(subnet, community, timeout)

	if len(devices) == 0 {
		log.Fatal("No active SNMP devices found in subnet")
	}

	// deviceDict := make(map[string]map[string]int)

	// Iterate over discovered devices
	for _, deviceIP := range devices {
		snmp := &gosnmp.GoSNMP{
			Target:    deviceIP,
			Port:      161,
			Community: "public",
			Version:   gosnmp.Version2c,
			Timeout:   time.Duration(5) * time.Second,
			Retries:   3,
		}

		err = snmp.Connect()
		if err != nil {
			log.Fatalf("SNMP Connection failed: %v", err)
		}
		defer snmp.Conn.Close()

		// deviceData, err := SNMPWalkExec(deviceIP, community)
		// if err != nil {
		// 	log.Fatalf("SNMP Walk failed: %v", err)
		// }

		// Print results
		// for oid, value := range deviceData {
		// 	fmt.Printf("%s = %s\n", oid, value)
		// }

		fmt.Println("Fetching sysObjectID...")

		// Get sysObjectID of the device
		sysObjectID, err := GetSysObjectID(snmp)
		if err != nil {
			log.Printf("Failed to get sysObjectID for %s: %v\n", deviceIP, err)
			continue
		}

		fmt.Printf("Device sysObjectID: %s\n", sysObjectID)

		matchingProfiles := FindMatchingProfiles(profiles, sysObjectID)
		if len(matchingProfiles) == 0 {
			log.Printf("No matching profile found for sysObjectID: %s", sysObjectID)
		}

		// // **🌟 Fetch all SNMP data once**
		// fmt.Println("Performing SNMP Walk for the entire device...")
		// deviceData, err := WalkDevice(snmp)
		// if err != nil {
		// 	log.Fatalf("SNMP Walk failed: %v", err)
		// }

		// fmt.Print(deviceData)

		// // // Store unique results
		// // results := make(map[string]string)

		// Walk through the SNMP device using all matched profiles
		for _, profile := range matchingProfiles {
			for _, metric := range profile.Metrics {
				if metric.Symbol != nil {
					response, err := SNMPGetExec(deviceIP, metric.Symbol.OID, "public")
					if err != nil {
						log.Fatalf("SNMP Exec failed: %v", err)
					}

					metricName := metric.Symbol.Name
					metricSplit := strings.SplitN(strings.SplitN(response, " = ", 2)[1], ": ", 2)
					metricType := metricSplit[0]
					metricValue := metricSplit[1]

					fmt.Printf("METRIC: %s | %s | %s\n", metricName, metricType, metricValue)

					// fmt.Print(response, "\n")
				} else if metric.Table != nil {
					for _, symbol := range metric.Symbols {
						if len(symbol.OID) > 1 {
							response, err := SNMPGetExec(deviceIP, symbol.OID, "public")
							if err != nil {
								log.Fatalf("SNMP Exec failed: %v", err)
							}

							if !strings.Contains(response, "No Such") || !strings.Contains(response, "at this OID") {

								fmt.Print(response, "\n")
								fmt.Print("FOUND TABLE REEEEE", deviceIP)
								os.Exit(-129)
							}
						}
					}
					// fmt.Print("something")
				}
				// if metric.Symbol != nil {
				// 	val, ok := deviceData[metric.Symbol.OID]
				// 	// If the key exists
				// 	if ok {
				// 		// Do something
				// 		// you have the symbol found here

				// 		metricName := metric.Symbol.Name
				// 		metricSplit := strings.SplitN(val, ": ", 2)
				// 		metricType := metricSplit[0]
				// 		metricValue := metricSplit[1]

				// 		fmt.Printf("METRIC: %s | %s | %s\n", metricName, metricType, metricValue)

				// 	}
				// 	// for key := range deviceData {
				// 	// 	if strings.Contains(key, metric.Symbol.OID) {
				// 	// 		fmt.Println("Found:", key)
				// 	// 	}
				// } else if metric.Table != nil {
				// 	fmt.Print("TABLE FOUND\n")
				// 	metricName := metric.Symbol.Name
				// 	metricSplit := strings.SplitN(val, ": ", 2)
				// 	metricType := metricSplit[0]
				// 	metricValue := metricSplit[1]

				// 	fmt.Printf("METRIC: %s | %s | %s\n", metricName, metricType, metricValue)
				// 	// os.Exit(19)

				// }

				// WalkOID(snmp, metric.Symbol.OID, metric.Symbol.Name, results)
				// // 			// deviceDict["0"]["1"] = 1
				// // 		} else if metric.Table != nil {
				// // 			for _, sym := range metric.Symbols {
				// // 				fmt.Printf("HERE %s\n", sym.OID)
				// // 				// os.Exit(1)
				// // 				// WalkOID(snmp, sym.OID, sym.Name, results)

				// // 				// todo build a savable index here, and call the func to update it. The dict would be metric_name and value. it can be MIB.name and if it is a table an index I guess
				// // 			}
				// // 		}
			}
		}
	}
}
