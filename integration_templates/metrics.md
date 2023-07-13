<!-- This gets a bit complex, so:
-->

<!-- if folding is set to true, wrap the whole string in a <details> element, so that it is collapsed, using metrics.folding.title as the summary -->

<!-- templated text -->
Metrics grouped by *scope*.

The scope defines the instance that the metric belongs to. An instance is uniquely identified by a set of labels.

<!-- if there is a metrics description, add it here-->
sample description

<!-- now, for global scope: -->
### Per ActiveMQ instance

<!-- scope description -->
These metrics refer to the entire monitored application.

<!-- then, if there is a labels array we need a table for it -->
| Label       | Description      |
|-------------|------------------|
<!-- iterate through the array and populate like: -->
| label.name  | label.description|

<!-- if there are no labels, say: -->
This scope has no labels.

<!-- templated text: -->
Metrics:

<!-- now for each metric, fill in a row in a table like: -->
| Metric      |                Dimensions                |    Unit     |
|-------------|:----------------------------------------:|:-----------:|
| metric.name | metric.dimensions array, comma separated | metric.unit |

<!-- if there is metrics.availability, we should introduce a new column, with name X/Y/Z where X,Y,Z are the strings in the array. Then for each row, for any of the availability strings included, add a "+", otherwise add a "-".-->

| Metric      |                Dimensions                |    Unit     | X/Y |
|-------------|:----------------------------------------:|:-----------:|:---:|
| metric.name | metric.dimensions array, comma separated | metric.unit | - + |

<!-- we could use more columns from the available fields, but we haven't agreed on what we want here so going with the way we have been doing it so far. -->

<!-- For every other scope, make a ### heading with the same logic: -->

### Per scope.name

...
