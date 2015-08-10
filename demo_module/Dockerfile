# Trytond 3.0
#
# Dockerfile used for presentation to Tampa Python Club
# in August 2015.  May not be suitable for other purposes.

FROM openlabs/tryton:3.0
MAINTAINER Jonathan Levy <jonl@advocatetax.com>

ADD . /opt/demo_module
RUN pip install -r /opt/demo_module/requirements.txt

# for demo, made code editable and sym link for auto-reloader
RUN pip install -e /opt/demo_module/
RUN ln -s /opt/demo_module /usr/local/lib/python2.7/dist-packages/trytond/modules/demo_module

# things to make the demo easier
#RUN apt-get update
RUN pip install --upgrade pip
RUN apt-get -y install vim ack-grep python-zmq
RUN pip install "ipython[notebook]"
RUN pip install pudb
ENV tm /usr/local/lib/python2.7/dist-packages/trytond/modules
ENV dm /opt/demo_module
WORKDIR /opt/demo_module

# 8888 for ipython notebook -- demo purposes only
EXPOSE 8888

# entrypoint is shell, for demo purposes
ENTRYPOINT ["/bin/bash"]

