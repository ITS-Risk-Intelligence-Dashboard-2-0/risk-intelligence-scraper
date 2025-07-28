FROM zenika/alpine-chrome

EXPOSE 9222

# You can add further customization here if needed
# For example, installing specific tools or libraries for your automation script

CMD ["chromium-browser", "--headless", "--remote-debugging-address=0.0.0.0", "--disable-host-check", "--remote-debugging-port=9222", "--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage", "--no-zygote", "--disable-background-networking"]
