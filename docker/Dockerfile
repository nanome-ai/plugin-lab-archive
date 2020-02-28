FROM continuumio/miniconda3

ENV ARGS=''

RUN conda install -c conda-forge poppler
RUN conda install -c bioconda wkhtmltopdf
RUN pip install nanome requests xmltodict pdf2image
RUN pip install imgkit

COPY . /app
WORKDIR /app

CMD python run.py ${ARGS}