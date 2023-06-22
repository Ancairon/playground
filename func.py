import csv
# import yaml
import os
from ruamel.yaml import YAML
import pandas as pd
import numpy as np



def csv_to_yaml(csv_file, yaml_file):
    metricslist = []
    data = {}
    data['metrics'] = {}
    data['metrics'] = {}
    
    with open(csv_file) as f:
        csv_data = csv.reader(f)
        next(csv_data)  # Skip the header
        metric = {}
        
        modules = pd.unique(pd.read_csv(csv_file)["module"])
        # return
        for row in csv_data:

            scope = row[1]
            if not scope:
                scope = "global"
            
            module = row[8]
            if not module:
                module = row[7]

            if module not in metric:
                metric[module]={}
            if scope not in metric[module]:
                labels = [{"name": x.strip(), "description": "TBD"} for x in row[6].split(',') if x]
                # for item in labels:
                #     label
                # metric[scope]= {"name":scope, "description":"TBD", "labels": labels, "metrics":[]}
                
                metric[module][scope]= {"name":scope, "description":"TBD", "labels": labels, "metrics":[]}
                # print(scope, metric.keys(), scope in metric.keys(), scope in metric)
            
            name = row[0]
            description = row[4]
            unit = row[3]
            dimensions = [{"name": n} for n in [x.strip() for x in row[2].split(',') if x] ]
            metric[module][scope]["metrics"].append({"name":name,"description":description,"unit":unit,"dimensions":dimensions})
            
            plugin = row[7]
        
        print(len(modules))
        if pd.isnull(modules):
            modules = [f"{plugin}"]

        for module in modules:
            metricslist.append(
                {"metrics":{"module":{"name":module},"folding":{"title": "Metrics", "enabled":False},"scope":metric[module]}})

            # print(name, description, unit,dimensions, labels)
    # sample = []
    # for element in metric.values():
    #     sample.append(element)

    # data["metrics"] = metric[scope]["metrics"]
            # print(metric)
    # data = {"metrics":{"folding":{"title": "Metrics", "enabled":False},"description":"TBD","scope":sample}}
    # data = {"metrics":{"folding":{"title": "Metrics", "enabled":False},"scope":sample}}
    print(metricslist)
    with open(yaml_file, 'w') as yf:
        # yaml.dump(data, yf, default_flow_style=False, sort_keys=False)

        yaml=YAML()
        yaml.default_flow_style = False
        yaml.sort_keys = False
        yaml.indent(mapping=2, sequence=4, offset=2)
        yaml.dump(metricslist, yf)

# print([x[0] for x in os.walk("./modules")])
dir = "./collectors/python.d.plugin"
for directory in next(os.walk(f'{dir}'))[1]:
    # directory = "apps.plugin"
    try:
        csv_to_yaml(f'{dir}/{directory}/metrics.csv', f'{dir}/{directory}/metadata.yaml')  
    except Exception as e:
        print("Exception", e)
    # exit()
        
