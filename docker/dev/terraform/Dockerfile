FROM hashicorp/terraform:1.15.8

RUN apk add --no-cache curl

WORKDIR /workspace

COPY main.tf variables.tf ./
COPY entrypoint.sh /usr/local/bin/terraform-pdns-seed

RUN chmod +x /usr/local/bin/terraform-pdns-seed

ENTRYPOINT ["/usr/local/bin/terraform-pdns-seed"]
