// Scans public/data/mcgill/ at build time is not feasible in Vite without a plugin.
// Instead, export a static index of the 29 valid files that can be used by a
// future dataset browser component.

export const MCGILL_INDEX = [
  { filename: 'love_is_a_battlefield_pat_benatar.json', title: 'Love Is A Battlefield', artist: 'Pat Benatar' },
  { filename: 'love_song_anne_murray.json', title: 'Love Song', artist: 'Anne Murray' },
  { filename: 'lovin_you_minnie_riperton.json', title: "Lovin' You", artist: 'Minnie Riperton' },
  { filename: 'loving_her_was_easier_than_anything_i_ll_ever_do_again_kris_kristofferson.json', title: "Loving Her Was Easier (Than Anything I'll Ever Do Again)", artist: 'Kris Kristofferson' },
  { filename: 'magic_man_heart.json', title: 'Magic Man', artist: 'Heart' },
  { filename: 'maneater_daryl_hall_john_oates.json', title: 'Maneater', artist: 'Daryl Hall & John Oates' },
  { filename: 'motownphilly_boyz_ii_men.json', title: 'Motownphilly', artist: 'Boyz II Men' },
  { filename: 'oh_my_angel_bertha_tillman.json', title: 'Oh My Angel', artist: 'Bertha Tillman' },
  { filename: 'one_way_or_another_blondie.json', title: 'One Way Or Another', artist: 'Blondie' },
  { filename: 'out_of_my_mind_johnny_tillotson.json', title: 'Out Of My Mind', artist: 'Johnny Tillotson' },
  { filename: 'riders_on_the_storm_the_doors.json', title: 'Riders On The Storm', artist: 'The Doors' },
  { filename: 'running_on_empty_jackson_browne.json', title: 'Running On Empty', artist: 'Jackson Browne' },
  { filename: 'she_thinks_i_still_care_elvis_presley.json', title: 'She Thinks I Still Care', artist: 'Elvis Presley' },
  { filename: 'shock_the_monkey_peter_gabriel.json', title: 'Shock The Monkey', artist: 'Peter Gabriel' },
  { filename: 'sittin_on_the_dock_of_the_bay_otis_redding.json', title: "(Sittin' On) The Dock Of The Bay", artist: 'Otis Redding' },
  { filename: 'starting_over_again_dolly_parton.json', title: 'Starting Over Again', artist: 'Dolly Parton' },
  { filename: 'sugar_shack_the_fireballs.json', title: 'Sugar Shack', artist: 'The Fireballs' },
  { filename: 'sunflower_glen_campbell.json', title: 'Sunflower', artist: 'Glen Campbell' },
  { filename: 'take_a_chance_on_me_abba.json', title: 'Take A Chance On Me', artist: 'Abba' },
  { filename: 'ten_percent_double_exposure.json', title: 'Ten Percent', artist: 'Double Exposure' },
  { filename: 'time_for_me_to_fly_reo_speedwagon.json', title: 'Time For Me To Fly', artist: 'REO Speedwagon' },
  { filename: 'torn_between_two_lovers_mary_macgregor.json', title: 'Torn Between Two Lovers', artist: 'Mary MacGregor' },
  { filename: 'trampled_under_foot_led_zeppelin.json', title: 'Trampled Under Foot', artist: 'Led Zeppelin' },
  { filename: 'unchained_melody_the_righteous_brothers.json', title: 'Unchained Melody', artist: 'The Righteous Brothers' },
  { filename: 'upside_down_diana_ross.json', title: 'Upside Down', artist: 'Diana Ross' },
  { filename: 'walk_right_in_the_moments.json', title: 'Walk Right In', artist: 'The Moments' },
  { filename: 'when_will_i_be_loved_linda_ronstadt.json', title: 'When Will I Be Loved', artist: 'Linda Ronstadt' },
  { filename: 'with_a_little_help_from_my_friends_joe_cocker.json', title: 'With A Little Help From My Friends', artist: 'Joe Cocker' },
  { filename: 'you_don_t_own_me_lesley_gore.json', title: "You Don't Own Me", artist: 'Lesley Gore' },
]

export const MCGILL_BASE_PATH = '/data/mcgill/'

