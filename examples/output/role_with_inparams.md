# Role role_with_inparams -- Ensure that a host on a storage system exists and has host WWPNs.

## Synopsis

Ensure that a host on a storage system exists and has host WWPNs\.

This role is idempotent\.


## Input Parameters

Input parameters for the role\.


**log_file** (str):

  Path name of log file\.


  Optional\.

**sar_type** (str):

  Type of the storage system\.


  Required\.

  Choices\: \[\&#39;ds8k\&#39;\, \&#39;fs9k\&#39;\]\.

**sar_hostname** (str):

  IP address or hostname of the storage system for logging in\.


  Required\.

**sar_username** (str):

  Username on the storage system\.


  Required\.

**sar_password** (str):

  Password on the storage system\.


  Required\.

**host_name** (str):

  Name of the host to be created\.


  Required\.

**host_wwpns** (list of str):

  WWPNs for the host\, in &lt;code&gt;hh\:hh\.\.\.&lt;/code&gt; or &lt;code&gt;hhhh\.\.\.&lt;/code&gt; format\.


  Required\.


## Output Parameters

Output parameters for the role\.

Their values are the names of variables to be set upon return from the role\.


**host_info** (str):

  Properties of the host \(specific to &lt;code&gt;sar\_type&lt;/code&gt;\)\.

  Type\: dict


  Optional\.


## Authors

* Andreas Maier

