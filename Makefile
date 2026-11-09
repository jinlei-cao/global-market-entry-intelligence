.PHONY: install demo fetch analyze test app
install:
	python -m pip install -e '.[app,dev]'
demo:
	marketintel demo
fetch:
	marketintel fetch
analyze:
	marketintel analyze
test:
	python -m pytest
app:
	streamlit run app/streamlit_app.py
