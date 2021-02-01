FROM neurodebian:buster-non-free

RUN export ND_ENTRYPOINT="/neurodocker/startup.sh" \
    && apt-get update -y \
    && apt-get install -y --no-install-recommends \
           apt-utils \
           bzip2 \
           ca-certificates \
           curl \
           locales \
           unzip \
           wget \
           python3 \
           python3-pip \
           python3-setuptools \
    && pip3 install wheel && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# nipype (1.5.1), dipy, trampolino
RUN pip3 install nipype==1.5.1 dipy trampolino

# MRtrix 3.0.0
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    g++ python python-numpy libeigen3-dev zlib1g-dev libqt4-opengl-dev \
    libgl1-mesa-dev libfftw3-dev libtiff5-dev \
    && wget https://github.com/MRtrix3/mrtrix3/archive/3.0.0.zip \
    && unzip 3.0.0.zip && cd mrtrix3-3.0.0 && ./configure -nogui \
    && ./build && cd .. && mv mrtrix3-3.0.0 /usr/share/mrtrix3 \
    && apt-get purge -y g++ python python-numpy && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/usr/share/mrtrix3/bin:${PATH}"
