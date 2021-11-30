FROM debian:bullseye

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install --no-install-recommends -y \
    apt-transport-https \
    bzip2 \
    ca-certificates strace \
    ssh

RUN apt-get update && apt-get install -y \
    curl \
    git \
    python3 \
    python-pkg-resources \
    vim \
    xz-utils

RUN \
  mkdir -p /home/cros-tast && \
  useradd cros-tast -d /home/cros-tast && \
  chown cros-tast: -R /home/cros-tast && \
  adduser cros-tast sudo && \
  echo "cros-tast ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
USER cros-tast
ENV HOME=/home/cros-tast
WORKDIR $HOME

RUN mkdir -p $HOME/trunk
RUN git clone \
    https://chromium.googlesource.com/chromiumos/chromite \
    $HOME/trunk/chromite
ENV PATH=$PATH:$HOME/trunk/chromite/scripts
RUN yes | gsutil update

RUN mkdir "$HOME/.ssh"
COPY --chown=cros-tast id_rsa "$HOME/.ssh/"
RUN chmod 0600 "$HOME/.ssh/id_rsa"
