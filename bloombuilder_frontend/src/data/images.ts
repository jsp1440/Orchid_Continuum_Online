import { ImageMetadata, TraitImageMetadata } from '@/types/bloombuilder';


export const herbariumImages: ImageMetadata[] = [
  { id: 'h1', url: 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762145798915_ba898292.webp', date: '1887-06-15', location: 'Vermont, USA', contributor: 'Dr. William Thompson', institution: 'Harvard Herbarium', type: 'herbarium' },
  { id: 'h2', url: 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762145800662_c181957a.webp', date: '1892-07-22', location: 'Maine, USA', contributor: 'Sarah Mitchell', institution: 'Yale Peabody Museum', type: 'herbarium' },
  { id: 'h3', url: 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762145802528_6252e690.webp', date: '1878-08-10', location: 'New Hampshire', contributor: 'Prof. Charles Greene', institution: 'Smithsonian', type: 'herbarium' },
  { id: 'h4', url: 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762145804272_36f54755.webp', date: '1901-06-30', location: 'Ontario, Canada', contributor: 'Emily Roberts', institution: 'Royal Ontario Museum', type: 'herbarium' },
  { id: 'h5', url: 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762145806013_277ed042.webp', date: '1895-07-18', location: 'Michigan, USA', contributor: 'Dr. James Foster', institution: 'Field Museum', type: 'herbarium' },
  { id: 'h6', url: 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762145807973_899faba5.webp', date: '1889-08-05', location: 'Wisconsin, USA', contributor: 'Margaret Davis', institution: 'Chicago Botanic Garden', type: 'herbarium' }
];

export const botanicalImages: ImageMetadata[] = [
  { id: 'b1', url: 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762145808738_05c39b51.webp', date: '1885', location: 'Brussels, Belgium', contributor: 'Lucien Linden (artist)', institution: 'Lindenia Iconographie', type: 'botanical' },
  { id: 'b2', url: 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762145810500_de1651f7.webp', date: '1891', location: 'Brussels, Belgium', contributor: 'P. de Pannemaeker', institution: 'Lindenia Iconographie', type: 'botanical' },
  { id: 'b3', url: 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762145812369_f26bf6e9.webp', date: '1898', location: 'Brussels, Belgium', contributor: 'A. Goossens', institution: 'Lindenia Iconographie', type: 'botanical' },
  { id: 'b4', url: 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762145814073_b2cce224.webp', date: '1903', location: 'Brussels, Belgium', contributor: 'J. Goffart', institution: 'Lindenia Iconographie', type: 'botanical' },
  { id: 'b5', url: 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762145815794_b813e801.webp', date: '1896', location: 'Brussels, Belgium', contributor: 'E. Severeyns', institution: 'Lindenia Iconographie', type: 'botanical' },
  { id: 'b6', url: 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762145817561_018c2e8d.webp', date: '1906', location: 'Brussels, Belgium', contributor: 'H. Bury', institution: 'Lindenia Iconographie', type: 'botanical' }
];

export const modernImages: ImageMetadata[] = [
  { id: 'm1', url: 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762145819149_0ce62db1.webp', date: '2023-06-12', location: 'Everglades, Florida', contributor: 'Maria Rodriguez', institution: 'iNaturalist', type: 'modern' },
  { id: 'm2', url: 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762145821071_77f21820.webp', date: '2024-07-08', location: 'Adirondacks, NY', contributor: 'John Chen', institution: 'GBIF', type: 'modern' },
  { id: 'm3', url: 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762145822769_9e46bb7a.webp', date: '2023-08-15', location: 'Acadia, Maine', contributor: 'Lisa Anderson', institution: 'EOL', type: 'modern' },
  { id: 'm4', url: 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762145824518_64a64924.webp', date: '2024-06-20', location: 'Algonquin, Ontario', contributor: 'David Kim', institution: 'iNaturalist', type: 'modern' },
  { id: 'm5', url: 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762145826858_6fd91036.webp', date: '2023-07-25', location: 'Isle Royale, MI', contributor: 'Sarah Johnson', institution: 'GBIF', type: 'modern' },
  { id: 'm6', url: 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762145828632_06494743.webp', date: '2024-08-02', location: 'Boundary Waters, MN', contributor: 'Michael Lee', institution: 'EOL', type: 'modern' }
];


export const traitGalleryImages: TraitImageMetadata[] = [
  { 
    id: 'tg1', 
    url: 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762150206219_92dd2100.webp', 
    spurLength: 'short', 
    petalColor: 'pink', 
    name: 'Short Spur Pink A', 
    description: 'Classic pink orchid with short spur adapted for short-tongued pollinators',
    characteristics: 'Compact spur (5-10mm), vibrant pink petals with darker veining, broad labellum',
    evolutionaryNotes: 'Short spurs evolved in response to bumblebee pollination. The compact structure allows easy access to nectar for insects with shorter proboscis.',
    pollinatorType: 'Bumblebees, short-tongued bees'
  },
  { 
    id: 'tg2', 
    url: 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762150207985_08e59341.webp', 
    spurLength: 'short', 
    petalColor: 'pink', 
    name: 'Short Spur Pink B', 
    description: 'Vibrant pink variant with compact spur structure',
    characteristics: 'Short spur (6-12mm), rose-pink coloration, reflexed petals for easy landing',
    evolutionaryNotes: 'This variant shows convergent evolution with other bee-pollinated flowers, developing similar color patterns and spur dimensions.',
    pollinatorType: 'Native bees, hover flies'
  },
  { 
    id: 'tg3', 
    url: 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762150208699_d2b347d7.webp', 
    spurLength: 'short', 
    petalColor: 'white', 
    name: 'Short Spur White A', 
    description: 'Pure white petals with short spur optimized for diurnal pollinators',
    characteristics: 'Compact spur (7-11mm), pristine white petals, yellow throat markings as nectar guides',
    evolutionaryNotes: 'White coloration attracts a broader range of pollinators. Short spur indicates adaptation to generalist pollination strategy.',
    pollinatorType: 'Various bees, butterflies'
  },
  { 
    id: 'tg4', 
    url: 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762150210491_852900b6.webp', 
    spurLength: 'short', 
    petalColor: 'white', 
    name: 'Short Spur White B', 
    description: 'Elegant white orchid with compact spur and prominent landing platform',
    characteristics: 'Short spur (5-9mm), pure white with subtle green tints, wide labellum',
    evolutionaryNotes: 'The combination of white petals and short spur suggests recent adaptation to changing pollinator communities in fragmented habitats.',
    pollinatorType: 'Small bees, syrphid flies'
  },
  { 
    id: 'tg5', 
    url: 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762150211190_74869dbc.webp', 
    spurLength: 'short', 
    petalColor: 'yellow', 
    name: 'Short Spur Yellow A', 
    description: 'Bright yellow orchid with short spur attracting bee pollinators',
    characteristics: 'Compact spur (6-10mm), golden yellow petals, UV-reflective patterns visible to bees',
    evolutionaryNotes: 'Yellow coloration with short spurs is a classic bee-pollination syndrome. UV patterns guide pollinators to nectar rewards.',
    pollinatorType: 'Honeybees, mining bees'
  },
  { 
    id: 'tg6', 
    url: 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762150213144_3194e0be.webp', 
    spurLength: 'short', 
    petalColor: 'yellow', 
    name: 'Short Spur Yellow B', 
    description: 'Golden yellow variant with compact structure and strong fragrance',
    characteristics: 'Short spur (7-12mm), bright yellow with orange accents, sweet scent',
    evolutionaryNotes: 'This form demonstrates how color and scent work synergistically with spur length to attract specific pollinator guilds.',
    pollinatorType: 'Bumblebees, carpenter bees'
  },
  { 
    id: 'tg7', 
    url: 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762150213946_a8a2c04e.webp', 
    spurLength: 'long', 
    petalColor: 'pink', 
    name: 'Long Spur Pink A', 
    description: 'Pink orchid with elongated spur specialized for sphinx moth pollination',
    characteristics: 'Extended spur (25-40mm), soft pink petals, narrow opening to exclude short-tongued visitors',
    evolutionaryNotes: 'Long spurs evolved through coevolution with long-tongued moths. This creates a specialized mutualism where only certain pollinators can access nectar.',
    pollinatorType: 'Sphinx moths, long-tongued hawk moths'
  },
  { 
    id: 'tg8', 
    url: 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762150215758_61999b5c.webp', 
    spurLength: 'long', 
    petalColor: 'pink', 
    name: 'Long Spur Pink B', 
    description: 'Rose-pink with distinctive long spur and nocturnal fragrance',
    characteristics: 'Long spur (30-45mm), rose-pink coloration intensifies at dusk, strong evening scent',
    evolutionaryNotes: 'The combination of long spur, pink color, and evening fragrance represents a textbook example of moth-pollination syndrome.',
    pollinatorType: 'Nocturnal moths, sphinx moths'
  },
  { 
    id: 'tg9', 
    url: 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762150216601_9b6e7ebd.webp', 
    spurLength: 'long', 
    petalColor: 'white', 
    name: 'Long Spur White A', 
    description: 'White orchid with extended spur visible in moonlight for moth attraction',
    characteristics: 'Extended spur (28-42mm), luminous white petals, reflective in low light conditions',
    evolutionaryNotes: 'White flowers with long spurs are classic moth-pollinated forms. The white color is highly visible to nocturnal pollinators in moonlight.',
    pollinatorType: 'Night-flying moths, sphinx moths'
  },
  { 
    id: 'tg10', 
    url: 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762150218294_098631ef.webp', 
    spurLength: 'long', 
    petalColor: 'white', 
    name: 'Long Spur White B', 
    description: 'Pristine white with long nectar spur and intense nocturnal fragrance',
    characteristics: 'Long spur (32-48mm), pure white, heavy sweet scent released at night',
    evolutionaryNotes: 'This represents an extreme specialization for moth pollination. The deep spur ensures only moths with matching proboscis length can pollinate.',
    pollinatorType: 'Long-tongued sphinx moths'
  },
  { 
    id: 'tg11', 
    url: 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762150219161_6312db5f.webp', 
    spurLength: 'long', 
    petalColor: 'yellow', 
    name: 'Long Spur Yellow A', 
    description: 'Yellow orchid with elongated spur for specialized butterfly pollination',
    characteristics: 'Extended spur (26-38mm), bright yellow with red spotting, diurnal fragrance',
    evolutionaryNotes: 'Yellow long-spurred orchids often attract long-tongued butterflies. This form bridges bee and moth pollination syndromes.',
    pollinatorType: 'Swallowtail butterflies, long-tongued skippers'
  },
  { 
    id: 'tg12', 
    url: 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762150221951_370f84be.webp', 
    spurLength: 'long', 
    petalColor: 'yellow', 
    name: 'Long Spur Yellow B', 
    description: 'Bright yellow with prominent long spur and complex nectar guides',
    characteristics: 'Long spur (29-44mm), golden yellow with intricate patterns, curved spur shape',
    evolutionaryNotes: 'The curved spur and complex patterning suggest fine-tuned coevolution with specific butterfly species, maximizing pollen transfer efficiency.',
    pollinatorType: 'Pipevine swallowtails, fritillary butterflies'
  }
];

