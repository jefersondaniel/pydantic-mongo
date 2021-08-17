release:
	python -m build
	twine upload dist/* --verbose
