import csv
import os
import ruamel.yaml
import pandas as pd
import numpy as np
from ruamel.yaml import YAML, representer
from collections import OrderedDict
import copy
from ruamel.yaml.scalarstring import LiteralScalarString, preserve_literal
# from ruamel.yaml.compat import string_types

# def walk_tree(base):

#     def test_wrap(v):
#         v = v.replace('\r\n', '\n').replace('\r', '\n').strip()
#         return v if len(v) < 72 else preserve_literal(v)

#     if isinstance(base, dict):
#         for k in base:
#             v = base[k]
#             if isinstance(v, string_types) and '\n' in v:
#                 base[k] = test_wrap(v)
#             else:
#                 walk_tree(v)
#     elif isinstance(base, list):
#         for idx, elem in enumerate(base):
#             if isinstance(elem, string_types) and '\n' in elem:
#                 base[idx] = test_wrap(elem)
#             else:
#                 walk_tree(elem)



class NoAliasDumper(ruamel.yaml.RoundTripRepresenter):
    def ignore_aliases(self, data):
        return True


module_count = 0


def scrape_alerts():
    dict = {}
    dir = "./health/health.d"
    for file in next(os.walk(f"{dir}"))[2]:
        i = 0
        if file.endswith(".conf"):
            filename = file
            file = open(f"{dir}/{file}", "r")

            whole_file = file.readlines()
            
            name = ""
            opsys = ""

            for index, line in enumerate(whole_file):
                nest_dict = {}
                i += 1

                # print("\n\nLINE:", line.strip("\n"))
                if not line.startswith("#"):
                    # print("Line is",line)
                    if "template:" in line or "alarm:" in line:
                        # print("Line", line)
                        name = line.split(": ", 1)[1].strip("\n")
                        # print(name)
                    if "on:" in line:
                        metric = line.split(": ", 1)[1].strip("\n")
                        # print(metric)
                    if "info:" in line:
                        # line= line.replace("\\", "ABC")
                        # print(line, line.endswith("\\\n"))
                        info = line.split(": ", 1)[1].strip("\n").strip("\\")
                        j = 1
                        while line.endswith("\\\n"):
                            # print("in")
                            line = whole_file[index+j]
                            j += 1
                            info += line.strip("\\\n").lstrip()
                            # print(line)
                            # return
                        # print(info,"\n")
                    if "os:" in line:
                        opsys = line.split(": ", 1)[1].strip("\n")

                    if name and (line == "\n" or i == len(whole_file)):
                        try:
                            # nest_dict = {"name": name, "metric": metric, "os": operating_sys, "info": info}
                            nest_dict = {
                                "name": f"{name}",
                                "link": f"https://github.com/netdata/netdata/blob/master/health/health.d/{filename}",
                                "metric": metric,
                                "info": info,
                            }

                            if opsys:
                                nest_dict['os'] = ruamel.yaml.scalarstring.DoubleQuotedScalarString(opsys)

                            try:
                                dict[metric]
                            except:
                                dict[metric] = []

                            dict[metric].append(nest_dict)
                            # print("OVER", dict)

                            name = None
                            info = None
                            opsys= None

                        except Exception as e:
                            print("Exception", e)
    return dict


def csv_to_yaml(csv_file, yaml_file, alert_dict):
    yaml = ruamel.yaml

    with open("collectors/metadata/single-module-template copy.yaml") as stream:
        try:
            template = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    global module_count

    metricslist = []
    data = {}
    data["metrics"] = {}

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
                    "description": ruamel.yaml.scalarstring.DoubleQuotedScalarString(""),
                    "labels": labels,
                    "metrics": [],
                }
                # print(scope, metric.keys(), scope in metric.keys(), scope in metric)

            metric[module][scope]["metrics"].append(
                {
                    "name": name,
                    # "availability": [],
                    "description": description,
                    # this double quoted thing ensures we got "" instead of ''
                    "unit": ruamel.yaml.scalarstring.DoubleQuotedScalarString(unit),
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

        try:
            if pd.isnull(modules.all()):
                # print("it is null", yaml_file)
                modules = [f"{plugin}"]
        except:
            pass
        try:
            if np.isnan(modules):
                # print("it is nan", yaml_file)
                modules = [f"{plugin}"]
        except:
            pass

        for module in modules:
            try:
                # print(module)
                module_count += 1
                scope_array = []
                for key in metric[module]:
                    scope_array.append(metric[module][key])

                dummy_template = {}
                dummy_template = template.copy()

                dummy_template["meta"]["module_name"] = module
                dummy_template["meta"]["plugin_name"] = plugin

                if plugin == module:
                    dummy_template["meta"]["monitored_instance"]["name"] = plugin.replace(".plugin", "")
                else:
                    dummy_template["meta"]["monitored_instance"]["name"] = plugin.replace(".plugin", "") + " " + module

                dummy_template["alerts"] = alerts[module]
                dummy_template["metrics"] = {
                    "folding": {"title": "Metrics", "enabled": False},
                    "description": ruamel.yaml.scalarstring.DoubleQuotedScalarString(""),
                    "availability": [],
                    "scopes": scope_array,
                }
                # print(dummy_template["meta"]["module_name"])
                metricslist.append(copy.deepcopy(dummy_template))
            except Exception as e:
                print(e)

        # print(metricslist)

        if len(modules) > 1:
            # print("multi", len(modules))
            finaldata = {"name": plugin, "modules": metricslist}

            with open(yaml_file.replace("metadata", "multi_metadata"), "w") as yf:
                # yaml.dump(data, yf, default_flow_style=False, sort_keys=False)

                yaml = YAML()
                yaml.width = 4096
                # yaml.default_flow_style = False
                yaml.Representer = NoAliasDumper
                yaml.sort_keys = False
                yaml.indent(mapping=2, sequence=4, offset=2)
                yaml.dump(finaldata, yf)
        else:
            # print("single")
            finaldata = metricslist

            with open(yaml_file, "w") as yf:
                # yaml.dump(data, yf, default_flow_style=False, sort_keys=False)

                yaml = YAML()
                yaml.width = 4096
                # yaml.default_flow_style = False
                yaml.Representer = NoAliasDumper
                yaml.sort_keys = False
                yaml.indent(mapping=2, sequence=4, offset=2)
                yaml.dump(finaldata[0], yf)



def csv_to_yaml_only_metrics(csv_file, yaml_file, alert_dict):
    yaml = ruamel.yaml

    # with open("collectors/metadata/single-module-template copy.yaml") as stream:
    #     try:
    #         template = yaml.safe_load(stream)
    #     except yaml.YAMLError as exc:
    #         print(exc)

    global module_count

    metricslist = []
    data = {}
    data["metrics"] = {}

    with open("collectors/metadata/single-module-template copy.yaml") as stream:
        try:
            dummy_template = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    with open(csv_file) as f:
        csv_data = csv.reader(f)
        next(csv_data)  # Skip the header
        metric = {}
        alerts = {}

        with open(yaml_file) as stream:
                    try:
                        template = yaml.safe_load(stream)
                    except yaml.YAMLError as exc:
                        print(exc)

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

            for element in template["metrics"]["scope"]:
                for item in element["metrics"]:
                    # print(item["name"])
                    if item["name"] == name:
                        item["chart_type"] = chart_type



            # print(template, scope)
            # template[scope]["metrics"].append(
            #     {
            #         "name": name,
            #         # "availability": [],
            #         "description": description,
            #         # this double quoted thing ensures we got "" instead of ''
            #         "unit": ruamel.yaml.scalarstring.DoubleQuotedScalarString(unit),
            #         "chart_type": chart_type,
            #         "dimensions": dimensions,
            #     }
            # )
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

        try:
            if pd.isnull(modules.all()):
                # print("it is null", yaml_file)
                modules = [f"{plugin}"]
        except:
            pass
        try:
            if np.isnan(modules):
                # print("it is nan", yaml_file)
                modules = [f"{plugin}"]
        except:
            pass

        # for module in modules:
        #     try:
        #         # print(module)
                # module_count += 1
                # scope_array = []
                # for key in metric[module]:
                #     scope_array.append(metric[module][key])

                # dummy_template = {}

                

                # dummy_template = template.copy()

                # dummy_template["meta"]["module_name"] = module
                # dummy_template["meta"]["plugin_name"] = plugin

                # if plugin == module:
                #     dummy_template["meta"]["monitored_instance"]["name"] = plugin.replace(".plugin", "")
                # else:
                #     dummy_template["meta"]["monitored_instance"]["name"] = plugin.replace(".plugin", "") + " " + module

                # dummy_template["alerts"] = alerts[module]
                # dummy_template["metrics"] = {
                #     "folding": {"title": "Metrics", "enabled": False},
                #     "description": ruamel.yaml.scalarstring.DoubleQuotedScalarString(""),
                #     "availability": [],
                #     "scopes": scope_array,
                # }
                # # print(dummy_template["meta"]["module_name"])
                # metricslist.append(copy.deepcopy(dummy_template))
        try:
            template["metrics"]["availability"] 
        except:
            template["metrics"]["availability"] = []
        
        
        template["metrics"]["scopes"] = template["metrics"].pop("scope")
        
        
        try:
            template["title"]

            for item in template["setup"]["prerequisites"]["list"]:
                item["description"] = item.pop("text")

            for item in template["setup"]["configuration"]["options"]["list"]:
                item["default_value"] = item.pop("default")

            for item in template["setup"]["configuration"]["examples"]["list"]:
                item["config"] = item.pop("data")

            try:
                template["setup"]["configuration"]["examples"]["folding"]
            except:
                template["setup"]["configuration"]["examples"]["folding"] = {"title": "Config options", "enabled": True}

            template["setup"]["configuration"]["file"] = {"name": ""}

            output = template
        except:
            print("AHH")
            dummy_template["metrics"] = template["metrics"]
            output = dummy_template



        with open(yaml_file, "w") as yf:
        # yaml.dump(data, yf, default_flow_style=False, sort_keys=False)

            yaml = YAML()
            # yaml.width = 4096
            yaml.default_flow_style = False
            yaml.Representer = NoAliasDumper
            yaml.sort_keys = False
            yaml.indent(mapping=2, sequence=4, offset=2)
            yaml.dump(output, yf)

            # except Exception as e:
            #     print(e)

        # # print(metricslist)

        # if len(modules) > 1:
        #     # print("multi", len(modules))
        #     finaldata = {"name": plugin, "modules": metricslist}

        #     with open(yaml_file.replace("metadata", "multi_metadata"), "w") as yf:
        #         # yaml.dump(data, yf, default_flow_style=False, sort_keys=False)

        #         yaml = YAML()
        #         yaml.width = 4096
        #         # yaml.default_flow_style = False
        #         yaml.Representer = NoAliasDumper
        #         yaml.sort_keys = False
        #         yaml.indent(mapping=2, sequence=4, offset=2)
        #         yaml.dump(finaldata, yf)
        # else:
        #     # print("single")
        #     finaldata = metricslist

        #     with open(yaml_file, "w") as yf:
        #         # yaml.dump(data, yf, default_flow_style=False, sort_keys=False)

        #         yaml = YAML()
        #         yaml.width = 4096
        #         # yaml.default_flow_style = False
        #         yaml.Representer = NoAliasDumper
        #         yaml.sort_keys = False
        #         yaml.indent(mapping=2, sequence=4, offset=2)
        #         yaml.dump(finaldata[0], yf)

dir = "./collectors"

for directory in next(os.walk(f"{dir}"))[1]:
    # print("\n"+directory)
    # directory = "freeipmi.plugin"
    alert_dict = scrape_alerts()
    try:
        csv_to_yaml(
            f"{dir}/{directory}/metrics.csv",
            f"{dir}/{directory}/metadata.yaml",
            alert_dict,
        )

    except Exception as e:
        print("Exception", e, directory)
    # break

dir = "./collectors/python.d.plugin"

for directory in next(os.walk(f"{dir}"))[1]:
    # directory = "beanstalk"

    alert_dict = scrape_alerts()
    try:
        csv_to_yaml(
            f"{dir}/{directory}/metrics.csv",
            f"{dir}/{directory}/metadata.yaml",
            alert_dict,
        )

    except Exception as e:
        print("Exception", e, directory)
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
        print("Exception", e, directory)

print(module_count)


# dir = "../go.d.plugin/modules"

# for directory in next(os.walk(f"{dir}"))[1]:
#     # directory = "docker_engine"
#     # print("\n"+directory)
#     alert_dict = scrape_alerts()
#     try:
#         csv_to_yaml_only_metrics(
#             f"{dir}/{directory}/metrics.csv",
#             f"{dir}/{directory}/metadata.yaml",
#             alert_dict,
#         )

#     except Exception as e:
#         print("Exception", e)
#     # break



# for root, dirs, files in os.walk("./collectors/python.d.plugin"):
#     dirs.sort()
#     if root == './collectors/python.d.plugin':
#         for d2i in dirs:
#             print("- [ ] "+d2i)
