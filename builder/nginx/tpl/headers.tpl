

HRS_Xframe: add_header X-Frame-Options "SAMEORIGIN" always;
HRS_Xframe_opts: [SAMEORIGIN,DENY,ALLOW-FROM {{ stie.hrs_opt_url }}]

HRS_max_size: client_max_body_size {{ site.hrs_max_size }};

HRS_Xcontent: add_header X-Content-Type-Options "nosniff" always;

HRS_Xxss: add_header X-XSS-Protection "1; mode=block" always;

HRS_Hsts: add_header Strict-Transport-Security "max-age={{ site.hrs_hsts_maxage}}; includeSubDomains" {{ site.hrs_hsts_subdmain }};

HRS_CacheControl: add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0";
{{ "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0", "public, max-age=3600"}}


HRS_CORS: add_header Access-Control-Allow-Origin "*";

HRS_Referrer: add_header Referrer-Policy "no-referrer-when-downgrade";
HRS_FrameAncestors: add_header Content-Security-Policy "frame-ancestors 'self'";
HRS_XPermittedCrossDomainPolicies: add_header X-Permitted-Cross-Domain-Policies "none";
HRS_XDownloadOptions: add_header X-Download-Options "noopen";
HRS_XDNSPrefetchControl: add_header X-DNS-Prefetch-Control "off";
HRS_XPoweredBy: add_header X-Powered-By "{{ site.powered }}";
HRS_ServerTokens: server_tokens {{ site.hrs_serverToken [no,yes] ;
HRS_XRequestID: add_header X-Request-ID $request_id;
