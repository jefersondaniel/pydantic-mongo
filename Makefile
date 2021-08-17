release:
	rm -Rf build dist
	python -m build
	twine upload dist/* --verbose
