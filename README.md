# Circle CI Container

[![CircleCI](https://circleci.com/gh/nanliu/circleci.svg?style=svg)](https://circleci.com/gh/nanliu/circleci)

Custom Circle CI container with:

* kubectl
* helm
* git-crypt
* terraform

# Development

* Install `pyenv` and `pyenv-virtualenv`:
```
brew install pyenv pyenv-virtualenv
```

* Setup circleci virtual environment:
```
pyenv install 2.7.14
pyenv virtualenv 2.7.14 circleci
pyenv activate circleci
```
