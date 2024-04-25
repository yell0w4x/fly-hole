# fly-hole

A publicly available [Pi-Hole](https://pi-hole.net) on [Fly.io](https://fly.io) by means of DNS-over-HTTPS (DoH).

For ease of installation visit https://yell0w4x.github.io/fly-hole/.
Feel free to use DoH `https://adsfree.fly.dev` I deployed for myself.
Test it by https://d3ward.github.io/toolz/adblock.html.

```
$ ./deploy --help
Adsfree

Fly.io based DNS app deploy script
A publicly available https://pi-hole.net on https://fly.io

Usage:
    ./deploy [OPTIONS]

Options:
    --new               Launch new application using fly.toml template
    --python            Use python DNS over HTTPS relay (set by default)
    --rust              Use rust DNS over HTTPS relay
    --app APP           Application name to use for deploy. Overrides one in toml file
    --debug             Set bash 'x' option
    --help              Show help message

Examples:
    Deploy new app.
    
        ./deploy --new --app myadsfree

    Redeploy 
        
        ./deploy

Note:
    This script allocates shared ipv4 and ipv6 addresses that cost nothing
    Dedicated ipv4 address costs $2/month
    
    Deployed services

    - DNS-over-HTTPS: https://myadsfree.fly.dev
      Free of charge as works with shared ipv4
      Test with `dnslookup google.com https://myadsfree.fly.dev`

    - DNS-over-TLS: tls://myadsfree.fly.dev:853 (dedicated ipv4 only)

    - Pi-hole admin: https://myadsfree.fly.dev:8443 (dedicated ipv4 only)
      To access within shared ipv4 issue `fly proxy 8080:80` after deployment
      then open in browser http://localhost:8080/admin
      Password is printed during the deployment
```

# Tests

To run end-to-end tests for python version issue `relay/run-tests` 
and for rust `relay/run-tests --rust` respectively.

```
$ relay/run-tests --help
Run e2e tests.

Usage:
    relay/run-tests [OPTIONS] [EXTRA_ARGS]

All the EXTRA_ARGS are passed to pytest

Options:
    --python    Run tests for python based SUT (set by default)
    --rust      Run tests for rust based SUT
    --debug     Build and use debug version of rust based relay
    --debug-sh  Set bash 'x' option
    --help      Show help message
```
