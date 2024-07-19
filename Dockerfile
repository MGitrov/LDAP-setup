FROM python

# Setting the working directory in the container.
WORKDIR /app

COPY app .

# Installing the "qrcode" with PIL functionality to handle image processing (the QR code).
RUN pip install Flask ldap3 pyotp qrcode[pil]

# Exposing port 5000 which is the port on which the Flask application runs.
EXPOSE 5000

# Will run the "app.py" script using Python.
CMD ["python", "app.py"]