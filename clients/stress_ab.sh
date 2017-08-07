
url=http://localhost:5000/login
ab -c $1 -n $2 -p post_data -k $url
