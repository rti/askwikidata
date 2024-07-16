# FROM rocm/pytorch-nightly:2024-06-04-rocm6.1
# FROM rocm/pytorch:rocm6.1_ubuntu22.04_py3.10_pytorch_2.4
FROM python:3.10

WORKDIR /workspace
COPY requirements.txt .

# RUN pip install --upgrade pip
# RUN pip install torch --index-url https://download.pytorch.org/whl/rocm6.0
# RUN pip install sentence-transformers aiofiles pandas tqdm psycopg[binary,pool]
# RUN pip install dask distributed dask-expr bokeh
RUN pip install -r requirements.txt

CMD ["sleep", "infinity"]

