FROM continuumio/miniconda3

ENV ARGS=''

RUN conda install -c conda-forge poppler
RUN conda install -c bioconda wkhtmltopdf
RUN conda install -c openbabel openbabel
RUN pip install nanome requests xmltodict pdf2image
RUN pip install imgkit

COPY . /app
RUN echo `ls /app`
WORKDIR /app
RUN mkdir --parents /root/Documents/nanome-plugins/lab-archives/
RUN mv /app/credentials.txt /root/Documents/nanome-plugins/lab-archives/

CMD python run.py ${ARGS}