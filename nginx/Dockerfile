#Use the official NGinx Alpine image for a small base
FROM nginx:alpine

# Remove the default Nginx configuration file
# This is important because we'll provide our own configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy your custom Nginx configuration file into the container
# This file will define how NGinx proxies requests to your backend and frontend services.
COPY default.conf /etc/nginx/conf.d/default.conf

# Expose port 80 (HTTP)
# This is the port NGinx will listen on for incoming web requests.
EXPOSE 80

# Command to run NGinx in the foreground
# This is necessary for Docker to keep the container running.
CMD ["nginx", "-g", "daemon off;"]
