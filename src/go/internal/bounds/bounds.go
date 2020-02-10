package bounds

import (
	"fmt"
	"log"

	"github.com/golang/geo/s2"
	"github.com/jonas-p/go-shp"
)

type Bounds struct {
	regions map[string]*region
}

func New(path string) (*Bounds, error) {
	r, err := shp.Open(path)
	if err != nil {
		return nil, err
	}
	regions := make(map[string]*region)
	for r.Next() {
		regionIdx := 0
		for i, f := range r.Fields() {
			if f.String() == "SOVEREIGN" {
				regionIdx = i
				break
			}
		}
		reg := r.Attribute(regionIdx)
		_, s := r.Shape()
		poly, ok := s.(*shp.Polygon)
		if !ok {
			return nil, fmt.Errorf("not a polygon")
		}
		var s2Pts []s2.Point
		for _, pt := range poly.Points {
			s2Pts = append(s2Pts, s2.PointFromLatLng(s2.LatLngFromDegrees(pt.Y, pt.X)))
		}
		p := s2.LoopFromPoints(s2Pts)
		if p.RectBound().Lng.IsFull() {
			p.Invert()
		}
		if _, ok = regions[reg]; !ok {
			regions[reg] = &region{}
		}
		regions[reg].polys = append(regions[reg].polys, p)
	}

	return &Bounds{regions: regions}, nil
}

func (b *Bounds) Contains(reg string, lat, lng float64) bool {
	r, ok := b.regions[reg]
	if !ok {
		log.Printf("region %s not found", reg)
		return false
	}
	return r.Contains(lat, lng)
}

func (b *Bounds) Regions() []string {
	var r []string
	for rg, _ := range b.regions {
		r = append(r, rg)
	}
	return r
}

type region struct {
	polys []*s2.Loop
}

func (r *region) Contains(lat, lng float64) bool {
	pt := s2.PointFromLatLng(s2.LatLngFromDegrees(lat, lng))
	for _, p := range r.polys {
		if p.ContainsPoint(pt) {
			return true
		}
	}
	return false
}
