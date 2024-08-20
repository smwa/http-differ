# HTTP Differ

This application logs changes to http endpoints. It emits error messages when an endpoint becomes unavailable, returns a non-success status code, or changes more than an acceptable amount.

If a log aggregator can alert you on stderr, this can be used to alert you to site changes
