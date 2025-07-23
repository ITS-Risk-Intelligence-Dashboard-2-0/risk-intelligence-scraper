FROM zenika/alpine-chrome

EXPOSE 9222

# You can add further customization here if needed
# For example, installing specific tools or libraries for your automation script

CMD ["chromium-browser", "--headless", "--remote-debugging-address=0.0.0.0", "--disable-host-check", "--remote-debugging-port=9222", "--disable-features=IsolateOrigins,site-per-process", "--host-resolver-rules='MAP browser 127.0.0.1'", "--disable-gpu", "--no-sandbox"]
