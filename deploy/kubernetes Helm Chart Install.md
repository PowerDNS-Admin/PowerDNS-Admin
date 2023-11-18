
### Kubernetes
There are three options to run PowerDNS-Admin in a kubernetes cluster. This currently assumes you already have an existing MySQL server setup and ready for use for powerdns-admin. This chart also supports Rancher chart questions, so that when installing in rancher you have a nice UI to enter all the parameters. You must package and push the chart to your own chart repository to use in rancher.

#### Option 1: Using helm chart with github repo
1. Register github repo with helm.  
   `helm repo add powerdns-admin https://raw.githubusercontent.com/johnwc/PowerDNS-Admin/master/deploy/`
2. Create and customize personalized installation settings file `myvalues.yaml`. Use existing [values.yaml](https://github.com/johnwc/PowerDNS-Admin/blob/master/deploy/PowerDNS-Admin/values.yaml) as template.
3. Install powerdns-admin  
   `helm install -n power-dns -f myvalues.yaml <install_name> powerdns-admin`

#### Option 2: Using helm chart local install
1. Clone the existing github repo to your local machine.  
   `git clone https://github.com/johnwc/PowerDNS-Admin`
2. Change directory into `./PowerDNS-Admin/deploy`
3. Install powerdns-admin  
   `helm install -n power-dns -f myvalues.yaml <install_name> ./PowerDNS-Admin/`

The notes output from the install will explain how to access PowerDNS-Admin. If you enable ingress and/or cert-manager it can be something like http://powerdns-admin.mydomain.com or https://powerdns-admin.mydomain.com, whatever hostname you set in `myvalues.yaml`.
