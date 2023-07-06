import csv

# import yaml
import os
import ruamel.yaml
import pandas as pd
import numpy as np
from ruamel.yaml import YAML, representer
from collections import OrderedDict


class NoAliasDumper(ruamel.yaml.RoundTripRepresenter):
    def ignore_aliases(self, data):
        return True

module_count = 0

def scrape_alerts():
    dict = {}
    dir = "./health/health.d"
    for file in next(os.walk(f"{dir}"))[2]:
        if file.endswith(".conf"):
            filename = file
            file = open(f"{dir}/{file}", "r")

            whole_file = file.readlines()
            i = 0
            name = ""

            for index, line in enumerate(whole_file):
                nest_dict = {}
                i += 1
                # print("\n\nLINE:", line.strip("\n"))
                if not line.startswith("#"):
                    # print("Line is",line)
                    if "template:" in line or "alarm:" in line:
                        # print("Line", line)
                        name = line.split(": ",1)[1].strip("\n")
                        # print(name)
                    if "on:" in line:
                        metric = line.split(": ",1)[1].strip("\n")
                        # print(metric)
                    if "info:" in line:
                        # line= line.replace("\\", "ABC")
                        # print(line, line.endswith("\\\n"))
                        info = line.split(": ",1)[1].strip("\n").strip("\\")
                        i=1
                        while line.endswith("\\\n"):
                          # print("in")
                          line = whole_file[index+i]
                          i+=1
                          info += line.strip("\\\n").lstrip()
                          # print(line)
                          # return
                        # print(info,"\n")
                    if "os:" in line:
                        opsys = line.split(": ",1)[1].strip("\n")

                    if name and (line == "\n" or i == len(whole_file) - 1):
                        try:
                            # nest_dict = {"name": name, "metric": metric, "os": operating_sys, "info": info}
                            nest_dict = {
                                "name": f"{name}",
                                "link": f"https://github.com/netdata/netdata/blob/master/health/health.d/{filename}",
                                "metric": metric,
                                "info": info,
                                "os": opsys
                            }

                            try:
                                dict[metric]
                            except:
                                dict[metric] = []

                            dict[metric].append(nest_dict)
                            # print("OVER", dict)

                            name = None
                            info = None

                        except Exception as e:
                            print("Exception", e)
    return dict


def csv_to_yaml(csv_file, yaml_file, alert_dict):
    yaml_string = """
name: Collector name
title: TBD Monitoring
duplicate_for_virtual_integrations:
  list:
    - "[TBD](link to TBD)"
    - "[TBD](link to TBD)"
overview:
  how_the_collector_works:
        # The CI will remove the curly brackets in the link, they are for replacing with the virtual integrations, to replace the link each time
    description: |
        This collector works by... {[TBD](link to TBD)} ...
  supported_platforms:
    description: |
        If this collector can't run on some platforms specify them here. Leave empty otherwise.
  multi-instance: true
  permissions:
    description: |
        if there are any notable permission requirements, eg running as root and so on, specify them here. Leave empty otherwise.
setup:
  prerequisites:
    list:
      - title: Prerequisite title for heading
        text: |
            - TBD
            - TBD
  behavior:
    auto_detection:
      description: |
        TBD
    limits:
      description: |
        TBD
    performance_impact:
      description: |
        TBD
  configuration:
    file:
      description: |
        which file the user has to edit. Example: go.d/apache.conf
    options:
      description: |
        TBD, use | and newline for multiline
      folding:
        title: Config options
        enabled: true
      list:
        - name: option name
          description: option description
          default: a number or a string
          required: true or false
    examples:
      folding:
        title: Config
        enabled: false
      list:
        - name: Basic / else describe what this example is about
          description: |
            A basic example configuration / describe your example
          data:
            jobs:
                - name: example
                  TBD: TBD
troubleshooting:
  problems:
    list:
      - name: possible troubleshooting title
        text: |
            describe the issue and the troubleshooting process
related_resources:
  integrations:
    list: [apache, weblog, httpcheck, etc]
        # This text will be added in the overview section
    overview_text: |
        give a simple description if there are any other collectors related to this collector. Example -> To get the most out of TBD, you can do XYZ with collectors X Y and Z. Check our related resources for more information.
    provide:
      description: |
        What info I can provide for other plugins that reference me? this will only be visible in their end, they will scrape this text. Example -> XYZ allows monitoring X Y Z metrics...
"""
    yaml = ruamel.yaml.YAML()
    template = {}

    global module_count
    
    metricslist = []
    data = {}
    data["metrics"] = {}
    # data['metrics'] = {}

    with open(csv_file) as f:
        csv_data = csv.reader(f)
        next(csv_data)  # Skip the header
        metric = {}
        alerts = {}

        modules = pd.unique(pd.read_csv(csv_file)["module"])
        # print(modules)
        # return

        for row in csv_data:
            name = row[0]
            description = row[4]
            unit = row[3]
            plugin = row[7]
            chart_type = row[5]
            dimensions = [{"name": n} for n in [x.strip() for x in row[2].split(",") if x]]
            scope = row[1]
            if not scope:
                scope = "global"

            module = row[8]
            if not module:
                module = row[7]

            if module not in metric:
                # print(module, "Not in dict", name)
                metric[module] = {}

            if scope not in metric[module]:
                labels = [{"name": x.strip(), "description": "TBD"} for x in row[6].split(",") if x]
                # for item in labels:
                #     label
                # metric[scope]= {"name":scope, "description":"TBD", "labels": labels, "metrics":[]}

                metric[module][scope] = {
                    "name": scope,
                    "description": "",
                    "labels": labels,
                    "metrics": [],
                }
                # print(scope, metric.keys(), scope in metric.keys(), scope in metric)

            metric[module][scope]["metrics"].append(
                {
                    "name": name,
                    "availability": [],
                    "description": description,
                    "unit": unit,
                    "chart_type": chart_type,
                    "dimensions": dimensions,
                }
            )
            # print(type(list(metric[module][scope])))

            
            try:
                alerts[module]
            except:
                alerts[module] = []

            try:
                alerts[module] += alert_dict[name]
            except Exception as e:
                pass
                # print("No alerts" , e)

            # print(name)
            # if name.startswith("system"):
            #     print(name, plugin)
            #     print(alert_dict[name])
            # metric[module][scope] = list(metric[module][scope])
        # print("Module length", len(modules))
        try:
            if pd.isnull(modules.any()):
                # print("it is null")
                modules = [f"{plugin}"]
        except:
            pass
        try:
            if np.isnan(modules):
                # print("it is null")
                modules = [f"{plugin}"]
        except:
            pass

        for module in modules:
            module_count+=1
            # print("Module", module)
            # metricslist.append({"name": module ,"metrics":{"folding":{"title": "Metrics", "enabled":False},"scope":metric[module]}})
            scope_array = []
            for key in metric[module]:
                scope_array.append(metric[module][key])

            template["module_name"] = module
            template["plugin_name"] = plugin
            template["alerts"] = alerts[module]
            template["metrics"] = {
                "folding": {"title": "Metrics", "enabled": False},
                "description": "",
                "availability": [],
                "scopes": scope_array,
            }
            metricslist.append(template.copy())
            # print(template)
            # print(metricslist[len(metricslist)-1])
            # print(metricslist)
            # metricslist.append({

            #                     "alerts": alerts[module],

            #                     "metrics":{"description":"some description for this section, or leave empty","folding":{"title": "Metrics", "enabled":False},"scope":metric[module]}})
        # print("end of loop")

        # dcit = {"name": module ,
        #                         "title": "TBD",
        #                         "overview": {"application": {"description": "TBD, use | and newline for multiline"},"collector": {"description": "TBD, use | and newline for multiline"}},
        #                         "setup": {"prerequisites": {"list": [{"title": "Prerequisite title for heading", "text": "List like with dashes, TBD, use | and newline for multiline"}]}},
        #                         "configuration": {"options": {"desription": "TBD, use | and newline for multiline","folding":{"title": "Config options", "enabled": True}, "list": [{"name": "option name", "description": "option description", "default":"a number or a string", "required": "true or false"}]}, "examples": {"folding":{"title": "Config", "enabled": False},"list": [{"name": "Basic / else describe what this example is about", "description": "A basic example configuration / describe your example", "data": "input the example data in yaml format"}]}},
        #                         "troubleshooting": {"problems": {"list": [{"name": "possible troubleshooting title", "text": "describe"}]}}}

        if len(modules) > 1:
            # print("multi", len(modules))
            finaldata = {"name": plugin, "modules": metricslist}

            with open(yaml_file, "w") as yf:
                # yaml.dump(data, yf, default_flow_style=False, sort_keys=False)

                yaml = YAML()
                yaml.default_flow_style = False
                yaml.Representer = NoAliasDumper
                yaml.sort_keys = False
                yaml.indent(mapping=2, sequence=4, offset=2)
                # yaml.indent(mapping=2,sequence=4)
                yaml.dump(finaldata, yf)
        else:
            # print("single")
            finaldata = metricslist

            with open(yaml_file, "w") as yf:
                # yaml.dump(data, yf, default_flow_style=False, sort_keys=False)

                yaml = YAML()
                yaml.default_flow_style = False
                yaml.Representer = NoAliasDumper
                yaml.sort_keys = False
                yaml.indent(mapping=2, sequence=4, offset=2)
                # yaml.indent(mapping=2,sequence=4)
                yaml.dump(finaldata[0], yf)

            # print(name, description, unit,dimensions, labels)
    # sample = []
    # for element in metric.values():
    #     sample.append(element)

    # data["metrics"] = metric[scope]["metrics"]
    # print(metric)
    # data = {"metrics":{"folding":{"title": "Metrics", "enabled":False},"description":"TBD","scope":sample}}
    # data = {"metrics":{"folding":{"title": "Metrics", "enabled":False},"scope":sample}}
    # print(metricslist)


print([x[0] for x in os.walk("./modules")])
dir = "./collectors"

for directory in next(os.walk(f"{dir}"))[1]:
    # directory = "proc.plugin"
    # print("\n"+directory)
    alert_dict = scrape_alerts()
    try:
        csv_to_yaml(
            f"{dir}/{directory}/metrics.csv",
            f"{dir}/{directory}/metadata.yaml",
            alert_dict,
        )
        
    except Exception as e:
        print("Exception", e)
    # break

dir = "./collectors/python.d.plugin"

for directory in next(os.walk(f"{dir}"))[1]:
    # directory = "beanstalk"
    # print("\n"+directory)
    alert_dict = scrape_alerts()
    try:
        csv_to_yaml(
            f"{dir}/{directory}/metrics.csv",
            f"{dir}/{directory}/metadata.yaml",
            alert_dict,
        )
        
    except Exception as e:
        print("Exception", e)
    # break
    # exit()

dir = "./collectors/charts.d.plugin"

for directory in next(os.walk(f"{dir}"))[1]:
    # directory = "freebsd.plugin"
    # print("\n"+directory)
    alert_dict = scrape_alerts()
    try:
        csv_to_yaml(
            f"{dir}/{directory}/metrics.csv",
            f"{dir}/{directory}/metadata.yaml",
            alert_dict,
        )
        
    except Exception as e:
        print("Exception", e)
print(module_count)
