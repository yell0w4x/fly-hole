# fly-hole

A publicly available [Pi-Hole](https://pi-hole.net) on [Fly.io](https://fly.io) by means of DNS-over-HTTPS (DoH).

Why to use DoH? To increase the overall security. 
Modern browsers deliver relatively new feature called ECH (Encrypted Client Hello) that relies on DoH. 
Without having DoH enabled browsers can't use ECH. Why it's crucial to use ECH? The ECH enables SNI (Server Name Indication) encryption. 
In nutshell SNI is the name of the web site you connect that is exposed in plain text without the ECH even 
in TLS based protocols like HTTPS. So that's one of the way how you get blocked from visiting some web sites.

For ease of installation visit https://yell0w4x.github.io/fly-hole/.
Feel free to use DoH `https://adsfree.fly.dev` I deployed for myself.
Test it here https://adblock-tester.com/. Check whether SNI is encrypted [here](https://www.cloudflare.com/en-gb/ssl/encrypted-sni/).
Or deploy your own DoH service with one simple command (fly.io free account required).

In Firefox open `about:preferences#privacy` go to Enable DNS over HTTPS section. 
Select Max Protection option and Custom provider, then put `https://adsfree.fly.dev` url into the textbox.

The details on this available [here](https://support.mozilla.org/en-US/kb/firefox-dns-over-https#:~:text=Synergized%20protection%3A%20DoH%20works%20by,defense%20against%20many%20online%20threats).

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
