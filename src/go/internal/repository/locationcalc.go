package repository

type LocationCalc struct {
	Name          string `pk:""`
	MinPoints     int
	ClusterRadius float64
	TweetFilter   string
}
