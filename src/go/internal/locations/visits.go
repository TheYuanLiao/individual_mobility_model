package locations

import (
	"sort"

	"github.com/ericwenn/mscthesis/src/go/internal/repository"
	cluster "github.com/smira/go-point-clustering"
)

type Options struct {
	ClusterRadius float64
	MinPoints     int
}

// Visits returns the most visited location.
// Can return a nil location if none was found.
func Visits(tweets []*repository.GeoTweet, options Options) *repository.Location {
	var pts cluster.PointList
	for _, t := range tweets {
		pts = append(pts, cluster.Point{t.Latitude, t.Longitude})
	}
	clusters, _ := cluster.DBScan(pts, options.ClusterRadius, options.MinPoints)
	var locations []*repository.Location
	for _, cl := range clusters {
		center, _, _ := cl.CentroidAndBounds(pts)
		locations = append(locations, &repository.Location{
			UserID:           tweets[0].UserID,
			Latitude:         center[0],
			Longitude:        center[1],
			Count:            len(cl.Points),
			PercentageTotal:  float64(len(cl.Points)) / float64(len(tweets)),
			RadiusKilometers: options.ClusterRadius,
		})
	}
	if len(locations) == 0 {
		return nil
	}
	sort.Slice(locations, func(i, j int) bool {
		return locations[i].Count > locations[j].Count
	})
	if len(locations) > 1 {
		locations[0].PercentageNext = float64(locations[1].Count) / float64(locations[0].Count)
	}
	return locations[0]
}
