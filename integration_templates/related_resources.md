<!-- this is a bit complex as well, you have to see if it will work from a code side of things. Here it goes: 

There is inside meta.related_resources.integrations.list a list of plugin names and module names, those should be keys to go and search into other integration yamls and pull meta.info_provided_to_referring_integrations from there. Then you can construct a list like:-->

<!-- templated text -->
You can further monitor this integration by using:
<!--  -->

- module_name
  
  module's info_provided_to_referring_integrations (info pulled from that module's yaml)
