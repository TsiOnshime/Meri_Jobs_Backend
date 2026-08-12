package repository

import "errors"


var ErrDuplicateJob = errors.New("job already exists")

var ErrJobNotFound = errors.New("job not found")
