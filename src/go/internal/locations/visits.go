package locations

import (
	"sort"

	"github.com/ericwenn/mscthesis/src/go/internal/twitterddl"
	cluster "github.com/smira/go-point-clustering"
)

// Visits returns the most visited location.
// Can return a nil location if none was found.
func Visits(tweets []*twitterddl.GeoTweet) *twitterddl.HomeLocation {
	const clusterRadius = 0.1
	var pts cluster.PointList
	for _, t := range tweets {
		pts = append(pts, cluster.Point{t.Latitude, t.Longitude})
	}
	clusters, _ := cluster.DBScan(pts, clusterRadius, 2)
	var locations []*twitterddl.HomeLocation
	for _, cl := range clusters {
		center, _, _ := cl.CentroidAndBounds(pts)
		locations = append(locations, &twitterddl.HomeLocation{
			UserID:           tweets[0].UserID,
			Latitude:         center[0],
			Longitude:        center[1],
			Count:            len(cl.Points),
			Percentage:       float64(len(cl.Points)) / float64(len(tweets)),
			RadiusKilometers: clusterRadius,
		})
	}
	if len(locations) == 0 {
		return nil
	}
	sort.Slice(locations, func(i, j int) bool {
		return locations[i].Count > locations[j].Count
	})
	return locations[0]
}
