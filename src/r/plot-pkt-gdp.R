# Title     : Visualize the multi-region results as compared with the ground truth
# Objective : PKT vs GDP/capita
# Created by: Yuan Liao
# Created on: 2021-02-09

library(dplyr)
library(ggplot2)
library(ggrepel)
library(ggpubr)
library(plyr)

# Model trips
df_dom <- read.csv('results/multi-region_stats_rid_6.csv', encoding = "UTF-8")
df_dom$city <- factor(df_dom$city, levels = c(0, 1))
df_dom$city <- mapvalues(df_dom$city, from = c(0, 1), to = c("Country", "City"))
region <- c('Australia', 'Austria', 'The Netherlands', 'Sweden',
            'Spain', 'Russian Federation')
df_dom$rg_gt <- ifelse(df_dom$country %in% region, df_dom$country, 'Other')

theme_set(
  theme_minimal() +
    theme(legend.position = c(0.8, 0.9))
  )

my_colors <- RColorBrewer::brewer.pal(7, "Dark2")
names(my_colors) <- c(region, 'Other')

g1 <- ggplot(df_dom, aes(x = gdp_capita, y = pkt_inland_yr_capita)) +
  labs(x='GDP (kUSD/capita/yr), nominal',
       y='Domestic PKT (1000 km/capita/yr)',
       title = '(a)') +
  geom_label_repel(aes(label = region_name, color=rg_gt),
                   alpha = 0.75, size = 2.5, label.size = NA) +
  geom_point(aes(shape = city, color=rg_gt), size=3) +
  scale_color_manual(name = "", values = my_colors) +
  scale_shape_discrete(name = "Region type") +
  guides(color = FALSE) +
  scale_x_continuous(limits = c(0, 75)) +
  scale_y_continuous(limits = c(0, 23)) +
  geom_smooth(method = "lm", formula = y ~ log(x),
              se = TRUE, color='gray', size = 0.05, alpha = 0.05)
#  theme(plot.margin=unit(c(0,-3.5,0,0), "cm")) # top, right, bottom, left


# Ground truth statistics
df_gt <- read.csv('results/multi-region_stats_gt.csv', encoding = "UTF-8-SIG")
names(df_gt) <- c('year', 'pkt_inland_yr_capita', 'country', 'gdp_capita', 'tw')
region <- c('Australia', 'Austria', 'The Netherlands', 'Sweden',
            'Spain', 'Russia')
names(my_colors) <- c(region, 'Other')

df_gt$rg_gt <- ifelse(df_gt$country %in% region, df_gt$country, 'Other')

df_gt_c <- df_gt[df_gt$rg_gt != 'Other', ]
df_gt_o <- df_gt[df_gt$rg_gt == 'Other', ]

df_gt_c_ends <- df_gt_c %>%
  group_by(country) %>%
  filter(year==max(year))

g2 <- ggplot() +
  labs(x='GDP (kUSD/capita/yr), real 2010 dollar',
       y='',
       title = '(b)') +
  geom_point(data = df_gt_o, aes(x = gdp_capita, y = pkt_inland_yr_capita),
             color=my_colors['Other'], size=0.3, alpha=0.3) +
  geom_point(data = df_gt_c, aes(x = gdp_capita, y = pkt_inland_yr_capita, color=rg_gt),
             size=2, alpha=0.5) +
  geom_label_repel(data = df_gt_c_ends, aes(x = gdp_capita, y = pkt_inland_yr_capita,
                                            label = country, color = rg_gt),
                   alpha = 0.75, size = 2.5, label.size = NA) +
  scale_color_manual(name = 'Country', values = my_colors) +
  scale_x_continuous(limits = c(0, 75)) +
  scale_y_continuous(limits = c(0, 23)) +
  guides(color = FALSE) +
  geom_smooth(method = "lm", formula = y ~ log(x),
              se = TRUE, color='gray', size = 0.05, alpha = 0.05)
#  theme(plot.margin=unit(c(0,0,0,-3.5), "cm"))# top, right, bottom, left

w <- 6 * 2
h <- 5
G <- ggarrange(g1, g2, ncol = 2, nrow = 1)
ggsave(filename = "figures/pkt-vs-gdp.png", plot=G,
       width = w, height = h, unit = "in", dpi = 300)