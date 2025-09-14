
server {
    listen 80;
    listen [::]:80;
    server_name {{ site.listen }};

    root {{ site.default_home }}/public_html

    index index.php 

    location {{ site.url }} {
        try_files $uri $uri/ /index.php?$query_string;
    }

    location ~ \.php$ {
        include fastcgi_params;
        fastcgi_pass unix:/run/php/php8.3-fpm.sock;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
    }

    location ^~ /.well-known/ {
        root {{ site.default_home }}/public_html/.well-known/;
        allow all;
        try_files $uri =404;
    }

    return 301 https://$host$request_uri;
    
    access_log /{{ site.default_home }}/logs/{{ site.domain }}django_http_access.log;
    error_log /{{ site.default_home }}/logs/{{ site.domain }}django_http_error.log;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name {{ site.listen }};

    {% if site.ssl %}
    ssl_certificate /etc/letsencrypt/live/{{ site.domain }}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{{ site.domain }}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    {% endif %}


    location ^~ /.well-known/ {
        root {{ site.default_home }}/public_html/.well-known/;
        allow all;
        try_files $uri =404;
    }


    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff";


    location ~* ^/(?!static/|media/).*\.(?:css|js)$ {
        expires -1;
        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0" always;
        try_files $uri =404;
    }
    
    # Favicon
    location = /favicon.ico {
        access_log off;
        log_not_found off;
        return 204;
    }

    location /static/ {
        alias {{site.django_path}}/static/;
        access_log off;
        try_files $uri =404;
        expires 5m;
        add_header Cache-Control "public";
    }

    location /media/ {
        alias {{site.django_path}}/media/;
        access_log off;
        expires 5m;
        try_files $uri =404;
        add_header Cache-Control "public";
    }

 

   location {{ site.url }} {
        proxy_pass http://127.0.0.1:{{ site.port }};
        # proxy basics
        proxy_http_version 1.1;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket upgrade (Channels/Daphne)
        proxy_set_header Upgrade    $http_upgrade;
        proxy_set_header Connection $connection_upgrade;

        # Timeouts suitable for SSE/WebSockets/long polls
        proxy_read_timeout  300s;
        proxy_send_timeout  300s;

        add_header X-Frame-Options "" always;
        proxy_hide_header  X-Frame-Options;
        add_header         X-Frame-Options "" always;

    }

    access_log /{{ site.default_home }}/logs/{{ site.domain }}django_https_access.log;
    error_log /{{ site.default_home }}/logs/{{ site.domain }}django_https_error.log;

}