# ActiveMQ monitoring

<!-- Costa said he doesn't want ## Overview here, but further below there has to be a level 3 heading, because making them level 2 headings would not make sense. If you think it is necessary to follow markdwon heirarchy, add ## Overview here-->

This collector gathers metrics about client requests, cache hits, and many more, while also providing metrics per each thread pool.

The [JMX Exporter](https://github.com/prometheus/jmx_exporter) is used to fetch metrics from a Cassandra instance and make them available at an endpoint like `http://127.0.0.1:7072/metrics`.

<!-- supported platforms 
Here, if any of the two arrays are populated, we should mention only that.
For example, if both are empty:
-->
This collector runs on all platforms Netdata supports.
<!-- if the include array is populated -->
This collector runs on X, Y, Z.
<!-- if the exclude array is populated -->
This collector runs on all platforms Netdata supports, except from X, Y, Z.

<!-- multi instance 
again, if true:-->
The collector supports collecting metrics from multiple instances of the integration, local or remote to the node the collector runs.

<!-- if it is false -->
The collector supports collecting metrics only from a single instance of the integration.

<!-- additional_permissions -->
add additional_permissions.description here.

<!-- related resources -> integrations -> list 
Here we want to have a small teaser of related stuff.

The list contains plugin name and module name, so the idea is to be able to go into that yaml, and pull out the monitored_instance.name, and wrap it in a link like {% relatedResource id="plugin_name.module_name" %}monitored_instance.name{% /relatedResource %} and then hopefully FE will be able to do the linking, Learn and Website will need some logic to function.-->

You can better monitor module_name by using our {% relatedResource id="plugin_name.module_name" %}monitored_instance.name{% /relatedResource %}, ..., integrations.

### Default Behavior

<!-- auto detection section -->
#### Auto-detection

add default_behavior.auto_detection.description here if any.

<!-- if empty, use a message like -->
There integration doesn't support auto-detection.

<!-- limits section -->
#### Limits

add default_behavior.limits.description here if any.

<!-- if empty, use a message like -->
There are no limits applied to this integration.

<!-- performance impact section -->
#### Performance Impact

add default_behavior.performance_impact.description here if any.

<!-- if empty, use a message like -->
There is no performance impact by using this integration.
