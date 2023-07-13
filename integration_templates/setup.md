<!-- prerequisites -->
### Prerequisites

<!-- here we got a list of level 4 headings, that have the description. So: -->
#### prerequisites.X_element.title

prerequisites.X_element.description

<!-- configuration section-->
### Configuration

<!-- file -->
#### File

The configuration filename is `configuration.file.title`.
<!-- if there is section_name also, append a bit to the sentence like: -->
and section `section_name` (section_name should have the brackets)


<!-- templated text -->
The file format is YAML. Generally, the format is:

```yaml
update_every: 1
autodetection_retry: 0
jobs:
  - name: some_name1
  - name: some_name1
```

You can edit the configuration file using the `edit-config` script from the
Netdata [config directory](https://github.com/netdata/netdata/blob/master/docs/configure/nodes.md#the-netdata-config-directory).

```bash
cd /etc/netdata 2>/dev/null || cd /opt/netdata/etc/netdata
sudo ./edit-config go.d/apache.conf
```
<!-- end of templated text -->

<!-- options section -->
#### Options

add setup.configuration.options.description here

<!-- here there is a folding element, so you can do a <details> element with summary the folding.title, if it is disabled, then don't do folding with details-->

<!-- then we need a table, like: -->

| Name | Description | Default | Required |
|:----:|-------------|:-------:|:--------:|
<!-- iterate through array and fill, when default and required are empty and false, make them an empty string. -->
| name | description |    1    |   yes    |
| name | description |         |          |


<!-- examples section -->
#### Examples

<!-- iterate and create one of these for every element in the list -->
##### name

description

<!-- respect folding here -->

```yaml
put `config` here
```

