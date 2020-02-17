package repository

type Location struct {
	CalcName string `idx:"calc"`
	UserID   int    `idx:"calc"`
	Type     string ``
	// Center of location
	Latitude  float64
	Longitude float64
	// Number of tweets at this location
	Count int
	// Percentage of total amount of tweets at this location
	PercentageTotal float64
	// Percentage of tweets at this location compared to next best fit.
	// 0 = perfect, 1 = bad
	PercentageNext   float64
	RadiusKilometers float64
}
