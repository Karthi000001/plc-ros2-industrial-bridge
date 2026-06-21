FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies for OpenPLC
RUN apt-get update && apt-get install -y \
    git wget curl build-essential \
    python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Clone and install OpenPLC Runtime v3
# OpenPLC supports IEC 61131-3: ST, LD, FBD, IL, SFC
RUN git clone https://github.com/thiagoralves/OpenPLC_v3.git /openplc
WORKDIR /openplc
RUN ./install.sh linux

# Port 8080: OpenPLC web IDE (browser → upload PLC programs)
# Port 502:  Modbus TCP server (Python bridge → read/write PLC variables)
EXPOSE 8080
EXPOSE 502

CMD ["/openplc/start_openplc.sh"]
