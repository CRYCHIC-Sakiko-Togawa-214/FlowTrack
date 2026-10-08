// Prepared from matched FiVE-Bench source videos and actual method outputs.
window.FLOWTRACK_CASES = [
  {
    "id": "beach-zebra",
    "videoId": "0081_A_horse",
    "editType": 1,
    "category": "subject",
    "before": "Horse",
    "after": "Zebra",
    "note": "A new subject. The same stride.",
    "width": 832,
    "height": 480,
    "duration": 5.063,
    "fps": "16/1",
    "frames": 81,
    "instruction": "Change the horse into a zebra.",
    "sourcePrompt": "A horse is galloping powerfully across a sandy beach, with waves crashing and seagulls flying overhead. The camera remains fixed, capturing the horse's dynamic motion.",
    "targetPrompt": "A zebra is galloping powerfully across a sandy beach, with waves crashing and seagulls flying overhead. The camera remains fixed, capturing the zebra's dynamic motion.",
    "media": {
      "source": {
        "src": "assets/videos/beach-zebra-source.mp4",
        "poster": "assets/posters/beach-zebra-source.jpg"
      },
      "ours": {
        "src": "assets/videos/beach-zebra-ours.mp4",
        "poster": "assets/posters/beach-zebra-ours.jpg"
      }
    }
  },
  {
    "id": "gym-panda",
    "videoId": "0042_gym-ball",
    "editType": 2,
    "category": "creative",
    "before": "Athlete",
    "after": "Panda",
    "note": "Carry the workout into a new character.",
    "width": 864,
    "height": 480,
    "duration": 4.313,
    "fps": "16/1",
    "frames": 69,
    "instruction": "Replace the man with a panda.",
    "sourcePrompt": "A man is performing a workout with a heavy gym ball, repeatedly lifting it above his head and then bringing it down in a controlled manner. The exercise takes place in a modern gym environment with motivational posters and equipment in the background. The camera remains stationary, focusing on the man's dynamic movements.",
    "targetPrompt": "A panda is performing a workout with a heavy gym ball, repeatedly lifting it above its head and then bringing it down in a controlled manner. The exercise takes place in a modern gym environment with motivational posters and equipment in the background. The camera remains stationary, focusing on the panda's dynamic movements.",
    "media": {
      "source": {
        "src": "assets/videos/gym-panda-source.mp4",
        "poster": "assets/posters/gym-panda-source.jpg"
      },
      "ours": {
        "src": "assets/videos/gym-panda-ours.mp4",
        "poster": "assets/posters/gym-panda-ours.jpg"
      }
    }
  },
  {
    "id": "playful-dog",
    "videoId": "0078_A_cat",
    "editType": 1,
    "category": "subject",
    "before": "Cat",
    "after": "Dog",
    "note": "Keep the toy, the room, and the playful motion.",
    "width": 832,
    "height": 480,
    "duration": 5.063,
    "fps": "16/1",
    "frames": 81,
    "instruction": "Change the cat into a dog.",
    "sourcePrompt": "A cat is pouncing playfully on a toy in a cozy living room, with a sofa and a window in the background. The camera remains fixed, focusing on the cat's playful behavior.",
    "targetPrompt": "A dog is pouncing playfully on a toy in a cozy living room, with a sofa and a window in the background. The camera remains fixed, focusing on the dog's playful behavior.",
    "media": {
      "source": {
        "src": "assets/videos/playful-dog-source.mp4",
        "poster": "assets/posters/playful-dog-source.jpg"
      },
      "ours": {
        "src": "assets/videos/playful-dog-ours.mp4",
        "poster": "assets/posters/playful-dog-ours.jpg"
      }
    }
  },
  {
    "id": "yellow-santa",
    "videoId": "0061_mbike-santa",
    "editType": 3,
    "category": "color",
    "before": "Red outfit",
    "after": "Yellow outfit",
    "note": "A local color edit in a moving scene.",
    "width": 864,
    "height": 480,
    "duration": 3.75,
    "fps": "16/1",
    "frames": 60,
    "instruction": "Change the color of the Santa Claus outfit from the original color to yellow.",
    "sourcePrompt": "A person dressed in a Santa Claus outfit is riding a motorcycle through a suburban area with trees and a shopping center in the background. The camera remains stationary, capturing the motorcycle as it moves smoothly along the road.",
    "targetPrompt": "A person dressed in a yellow Santa Claus outfit is riding a motorcycle through a suburban area with trees and a shopping center in the background. The camera remains stationary, capturing the motorcycle as it moves smoothly along the road.",
    "media": {
      "source": {
        "src": "assets/videos/yellow-santa-source.mp4",
        "poster": "assets/posters/yellow-santa-source.jpg"
      },
      "ours": {
        "src": "assets/videos/yellow-santa-ours.mp4",
        "poster": "assets/posters/yellow-santa-ours.jpg"
      }
    }
  },
  {
    "id": "red-motorbike",
    "videoId": "0038_motorbike",
    "editType": 3,
    "category": "color",
    "before": "Motorbike",
    "after": "Red motorbike",
    "note": "Change the color along the original ride.",
    "width": 864,
    "height": 480,
    "duration": 2.688,
    "fps": "16/1",
    "frames": 43,
    "instruction": "Add the color red to the motorbike.",
    "sourcePrompt": "A motorbike with two riders is cruising along a scenic mountain road, surrounded by lush green forests and distant rocky peaks. The camera remains stationary, capturing the motorbike's smooth passage past vibrant flower pots lining the roadside.",
    "targetPrompt": "A red motorbike with two riders is cruising along a scenic mountain road, surrounded by lush green forests and distant rocky peaks. The camera remains stationary, capturing the motorbike's smooth passage past vibrant flower pots lining the roadside.",
    "media": {
      "source": {
        "src": "assets/videos/red-motorbike-source.mp4",
        "poster": "assets/posters/red-motorbike-source.jpg"
      },
      "ours": {
        "src": "assets/videos/red-motorbike-ours.mp4",
        "poster": "assets/posters/red-motorbike-ours.jpg"
      }
    }
  },
  {
    "id": "pink-butterfly",
    "videoId": "0045_butterfly",
    "editType": 3,
    "category": "color",
    "before": "Blue butterfly",
    "after": "Pink butterfly",
    "note": "A small subject. A precise color change.",
    "width": 864,
    "height": 480,
    "duration": 5.0,
    "fps": "16/1",
    "frames": 80,
    "instruction": "Change the color of the butterfly from blue to pink.",
    "sourcePrompt": "A vibrant blue butterfly flutters gracefully around a leafy plant in a sunlit garden. The camera remains fixed, capturing the delicate movements of the butterfly against a backdrop of greenery and a rustic stone structure.",
    "targetPrompt": "A vibrant pink butterfly flutters gracefully around a leafy plant in a sunlit garden. The camera remains fixed, capturing the delicate movements of the butterfly against a backdrop of greenery and a rustic stone structure.",
    "media": {
      "source": {
        "src": "assets/videos/pink-butterfly-source.mp4",
        "poster": "assets/posters/pink-butterfly-source.jpg"
      },
      "ours": {
        "src": "assets/videos/pink-butterfly-ours.mp4",
        "poster": "assets/posters/pink-butterfly-ours.jpg"
      }
    }
  },
  {
    "id": "plush-dog",
    "videoId": "0089_A_dog",
    "editType": 4,
    "category": "material",
    "before": "Dog",
    "after": "Plush dog",
    "note": "A softer appearance by the same shoreline.",
    "width": 832,
    "height": 480,
    "duration": 5.063,
    "fps": "16/1",
    "frames": 81,
    "instruction": "Replace the real dog with a plush dog.",
    "sourcePrompt": "A dog is wagging its tail excitedly while sitting on a sandy beach with waves crashing in the background. The camera remains fixed, focusing on the dog's joyful expression.",
    "targetPrompt": "A plush dog is wagging its tail excitedly while sitting on a sandy beach with waves crashing in the background. The camera remains fixed, focusing on the dog's joyful expression.",
    "media": {
      "source": {
        "src": "assets/videos/plush-dog-source.mp4",
        "poster": "assets/posters/plush-dog-source.jpg"
      },
      "ours": {
        "src": "assets/videos/plush-dog-ours.mp4",
        "poster": "assets/posters/plush-dog-ours.jpg"
      }
    }
  },
  {
    "id": "coastal-jeep",
    "videoId": "0096_A_car",
    "editType": 1,
    "category": "subject",
    "before": "Car",
    "after": "Jeep",
    "note": "Follow the source along a winding coast.",
    "width": 832,
    "height": 480,
    "duration": 5.063,
    "fps": "16/1",
    "frames": 81,
    "instruction": "Change 'car' to 'jeep'.",
    "sourcePrompt": "A car is driving along a winding coastal road with waves crashing against the cliffs below. The camera tracks the car's movement with a fast pan.",
    "targetPrompt": "A jeep is driving along a winding coastal road with waves crashing against the cliffs below. The camera tracks the jeep's movement with a fast pan.",
    "media": {
      "source": {
        "src": "assets/videos/coastal-jeep-source.mp4",
        "poster": "assets/posters/coastal-jeep-source.jpg"
      },
      "ours": {
        "src": "assets/videos/coastal-jeep-ours.mp4",
        "poster": "assets/posters/coastal-jeep-ours.jpg"
      }
    }
  },
  {
    "id": "bear-panda",
    "videoId": "0009_bear",
    "editType": 1,
    "category": "subject",
    "before": "Bear",
    "after": "Panda",
    "note": "A new subject with the same movement.",
    "width": 864,
    "height": 480,
    "duration": 5.125,
    "fps": "16/1",
    "frames": 82,
    "instruction": "Replace the brown bear with a panda.",
    "sourcePrompt": "A large brown bear is walking slowly across a rocky terrain in a zoo enclosure, surrounded by stone walls and scattered greenery. The camera remains fixed, capturing the bear's deliberate movements.",
    "targetPrompt": "A large panda is walking slowly across a rocky terrain in a zoo enclosure, surrounded by stone walls and scattered greenery. The camera remains fixed, capturing the panda's deliberate movements.",
    "media": {
      "source": {
        "src": "assets/videos/bear-panda-source.mp4",
        "poster": "assets/posters/bear-panda-source.jpg"
      },
      "ours": {
        "src": "assets/videos/bear-panda-ours.mp4",
        "poster": "assets/posters/bear-panda-ours.jpg"
      }
    }
  },
  {
    "id": "boat-yacht",
    "videoId": "0058_boat",
    "editType": 1,
    "category": "subject",
    "before": "Fishing boat",
    "after": "Yacht",
    "note": "Change the vessel while preserving the wake.",
    "width": 864,
    "height": 480,
    "duration": 4.688,
    "fps": "16/1",
    "frames": 75,
    "instruction": "Replace 'fishing boat' with 'yacht'.",
    "sourcePrompt": "A white fishing boat is cruising steadily across the calm blue waters near a rocky shoreline with sparse vegetation and a few white buildings in the background. The camera remains fixed, capturing the boat's smooth movement and the gentle waves it creates.",
    "targetPrompt": "A white yacht is cruising steadily across the calm blue waters near a rocky shoreline with sparse vegetation and a few white buildings in the background. The camera remains fixed, capturing the yacht's smooth movement and the gentle waves it creates.",
    "media": {
      "source": {
        "src": "assets/videos/boat-yacht-source.mp4",
        "poster": "assets/posters/boat-yacht-source.jpg"
      },
      "ours": {
        "src": "assets/videos/boat-yacht-ours.mp4",
        "poster": "assets/posters/boat-yacht-ours.jpg"
      }
    }
  },
  {
    "id": "dog-rabbit",
    "videoId": "0057_dog",
    "editType": 1,
    "category": "subject",
    "before": "Retriever",
    "after": "Rabbit",
    "note": "A complete subject change in a moving scene.",
    "width": 864,
    "height": 480,
    "duration": 3.75,
    "fps": "16/1",
    "frames": 60,
    "instruction": "Replace the golden retriever with a rabbit.",
    "sourcePrompt": "A golden retriever is sniffing the ground in a dry, grassy yard with a wooden fence in the background. The camera follows the dog slowly as it moves across the yard.",
    "targetPrompt": "A rabbit is sniffing the ground in a dry, grassy yard with a wooden fence in the background. The camera follows the rabbit slowly as it moves across the yard.",
    "media": {
      "source": {
        "src": "assets/videos/dog-rabbit-source.mp4",
        "poster": "assets/posters/dog-rabbit-source.jpg"
      },
      "ours": {
        "src": "assets/videos/dog-rabbit-ours.mp4",
        "poster": "assets/posters/dog-rabbit-ours.jpg"
      }
    }
  },
  {
    "id": "swan-duck",
    "videoId": "0094_A_swan",
    "editType": 1,
    "category": "subject",
    "before": "Swan",
    "after": "Duck",
    "note": "Preserve the water motion and reflections.",
    "width": 832,
    "height": 480,
    "duration": 5.063,
    "fps": "16/1",
    "frames": 81,
    "instruction": "Replace the swan with a duck.",
    "sourcePrompt": "A swan is swimming gracefully across a still pond surrounded by reeds. The camera remains fixed, capturing the swan's elegant movements.",
    "targetPrompt": "A duck is swimming gracefully across a still pond surrounded by reeds. The camera remains fixed, capturing the duck's elegant movements.",
    "media": {
      "source": {
        "src": "assets/videos/swan-duck-source.mp4",
        "poster": "assets/posters/swan-duck-source.jpg"
      },
      "ours": {
        "src": "assets/videos/swan-duck-ours.mp4",
        "poster": "assets/posters/swan-duck-ours.jpg"
      }
    }
  },
  {
    "id": "bear-dinosaur",
    "videoId": "0009_bear",
    "editType": 2,
    "category": "creative",
    "before": "Bear",
    "after": "Dinosaur",
    "note": "Push the subject into a new visual world.",
    "width": 864,
    "height": 480,
    "duration": 5.125,
    "fps": "16/1",
    "frames": 82,
    "instruction": "Replace the bear with a dinosaur.",
    "sourcePrompt": "A large brown bear is walking slowly across a rocky terrain in a zoo enclosure, surrounded by stone walls and scattered greenery. The camera remains fixed, capturing the bear's deliberate movements.",
    "targetPrompt": "A large dinosaur is walking slowly across a rocky terrain in a zoo enclosure, surrounded by stone walls and scattered greenery. The camera remains fixed, capturing the dinosaur's deliberate movements.",
    "media": {
      "source": {
        "src": "assets/videos/bear-dinosaur-source.mp4",
        "poster": "assets/posters/bear-dinosaur-source.jpg"
      },
      "ours": {
        "src": "assets/videos/bear-dinosaur-ours.mp4",
        "poster": "assets/posters/bear-dinosaur-ours.jpg"
      }
    }
  },
  {
    "id": "glider-dragon",
    "videoId": "0006_paragliding",
    "editType": 2,
    "category": "creative",
    "before": "Paraglider",
    "after": "Dragon",
    "note": "Transform the airborne subject and keep its path.",
    "width": 864,
    "height": 480,
    "duration": 4.375,
    "fps": "16/1",
    "frames": 70,
    "instruction": "Replace the paraglider with a dragon.",
    "sourcePrompt": "A paraglider is soaring gracefully over a lush, green landscape with a quaint village nestled among the hills. The camera remains stationary, capturing the serene flight against the backdrop of rolling hills and scattered houses.",
    "targetPrompt": "A dragon is soaring gracefully over a lush, green landscape with a quaint village nestled among the hills. The camera remains stationary, capturing the serene flight against the backdrop of rolling hills and scattered houses.",
    "media": {
      "source": {
        "src": "assets/videos/glider-dragon-source.mp4",
        "poster": "assets/posters/glider-dragon-source.jpg"
      },
      "ours": {
        "src": "assets/videos/glider-dragon-ours.mp4",
        "poster": "assets/posters/glider-dragon-ours.jpg"
      }
    }
  },
  {
    "id": "dog-robot",
    "videoId": "0057_dog",
    "editType": 2,
    "category": "creative",
    "before": "Retriever",
    "after": "Robotic dog",
    "note": "A robotic redesign with the original motion.",
    "width": 864,
    "height": 480,
    "duration": 3.75,
    "fps": "16/1",
    "frames": 60,
    "instruction": "Replace the golden retriever with a robotic dog.",
    "sourcePrompt": "A golden retriever is sniffing the ground in a dry, grassy yard with a wooden fence in the background. The camera follows the dog slowly as it moves across the yard.",
    "targetPrompt": "A robotic dog is sniffing the ground in a dry, grassy yard with a wooden fence in the background. The camera follows the robotic dog slowly as it moves across the yard.",
    "media": {
      "source": {
        "src": "assets/videos/dog-robot-source.mp4",
        "poster": "assets/posters/dog-robot-source.jpg"
      },
      "ours": {
        "src": "assets/videos/dog-robot-ours.mp4",
        "poster": "assets/posters/dog-robot-ours.jpg"
      }
    }
  },
  {
    "id": "wooden-motorbike",
    "videoId": "0038_motorbike",
    "editType": 4,
    "category": "material",
    "before": "Motorbike",
    "after": "Wooden motorbike",
    "note": "Change the material through a fast ride.",
    "width": 864,
    "height": 480,
    "duration": 2.688,
    "fps": "16/1",
    "frames": 43,
    "instruction": "Change the motorbike to a wooden motorbike.",
    "sourcePrompt": "A motorbike with two riders is cruising along a scenic mountain road, surrounded by lush green forests and distant rocky peaks. The camera remains stationary, capturing the motorbike's smooth passage past vibrant flower pots lining the roadside.",
    "targetPrompt": "A wooden motorbike with two riders is cruising along a scenic mountain road, surrounded by lush green forests and distant rocky peaks. The camera remains stationary, capturing the motorbike's smooth passage past vibrant flower pots lining the roadside.",
    "media": {
      "source": {
        "src": "assets/videos/wooden-motorbike-source.mp4",
        "poster": "assets/posters/wooden-motorbike-source.jpg"
      },
      "ours": {
        "src": "assets/videos/wooden-motorbike-ours.mp4",
        "poster": "assets/posters/wooden-motorbike-ours.jpg"
      }
    }
  },
  {
    "id": "helicopter-ufo",
    "videoId": "0035_helicopter",
    "editType": 2,
    "category": "creative",
    "before": "Helicopter",
    "after": "UFO",
    "note": "A graphic transformation in an open sky.",
    "width": 864,
    "height": 480,
    "duration": 3.063,
    "fps": "16/1",
    "frames": 49,
    "instruction": "Change the helicopter into a UFO, and change the rotors spinning rapidly into the UFO's lights spinning rapidly.",
    "sourcePrompt": "A helicopter is hovering above a helipad at an airport, with a ground crew member in a reflective vest walking towards it. The camera remains stationary, capturing the scene with the helicopter's rotors spinning rapidly.",
    "targetPrompt": "A UFO is hovering above a helipad at an airport, with a ground crew member in a reflective vest walking towards it. The camera remains stationary, capturing the scene with the UFO's lights spinning rapidly.",
    "media": {
      "source": {
        "src": "assets/videos/helicopter-ufo-source.mp4",
        "poster": "assets/posters/helicopter-ufo-source.jpg"
      },
      "ours": {
        "src": "assets/videos/helicopter-ufo-ours.mp4",
        "poster": "assets/posters/helicopter-ufo-ours.jpg"
      }
    }
  },
  {
    "id": "eagle-nest",
    "videoId": "0097_A_bird",
    "editType": 1,
    "category": "subject",
    "before": "Bird",
    "after": "Eagle",
    "note": "A precise subject change while the nest building continues.",
    "width": 832,
    "height": 480,
    "duration": 5.063,
    "fps": "16/1",
    "frames": 81,
    "instruction": "Change the bird to an eagle.",
    "sourcePrompt": "A bird is building a nest in a tree, carefully arranging twigs and leaves. The camera zooms in slowly to capture the bird's meticulous work.",
    "targetPrompt": "An eagle is building a nest in a tree, carefully arranging twigs and leaves. The camera zooms in slowly to capture the bird's meticulous work.",
    "media": {
      "source": {
        "src": "assets/videos/eagle-nest-source.mp4",
        "poster": "assets/posters/eagle-nest-source.jpg"
      },
      "ours": {
        "src": "assets/videos/eagle-nest-ours.mp4",
        "poster": "assets/posters/eagle-nest-ours.jpg"
      }
    }
  },
  {
    "id": "pink-burnout",
    "videoId": "0014_burnout",
    "editType": 3,
    "category": "color",
    "before": "Black car",
    "after": "Pink car",
    "note": "Change the car color through smoke and motion.",
    "width": 864,
    "height": 480,
    "duration": 4.5,
    "fps": "16/1",
    "frames": 72,
    "instruction": "Change the color of the car from black to pink.",
    "sourcePrompt": "A black car is performing a burnout, creating thick clouds of smoke on a track surrounded by a crowd of spectators. The camera remains stationary, capturing the car's spinning motion and the audience's reactions.",
    "targetPrompt": "A pink car is performing a burnout, creating thick clouds of smoke on a track surrounded by a crowd of spectators. The camera remains stationary, capturing the car's spinning motion and the audience's reactions.",
    "media": {
      "source": {
        "src": "assets/videos/pink-burnout-source.mp4",
        "poster": "assets/posters/pink-burnout-source.jpg"
      },
      "ours": {
        "src": "assets/videos/pink-burnout-ours.mp4",
        "poster": "assets/posters/pink-burnout-ours.jpg"
      }
    }
  },
  {
    "id": "yellow-golf",
    "videoId": "0013_golf",
    "editType": 3,
    "category": "color",
    "before": "Black shirt",
    "after": "Yellow shirt",
    "note": "A local wardrobe color change on the move.",
    "width": 864,
    "height": 480,
    "duration": 4.938,
    "fps": "16/1",
    "frames": 79,
    "instruction": "Change the color of the man's shirt from black to yellow.",
    "sourcePrompt": "A man in a black shirt and shorts walks towards a golf cart parked on a lush green golf course. He gets into the cart, starts it, and begins to drive away, with a set of golf clubs visible in the back. The camera remains stationary, capturing the serene golf course environment with trees and mountains in the background.",
    "targetPrompt": "A man in a yellow shirt and shorts walks towards a golf cart parked on a lush green golf course. He gets into the cart, starts it, and begins to drive away, with a set of golf clubs visible in the back. The camera remains stationary, capturing the serene golf course environment with trees and mountains in the background.",
    "media": {
      "source": {
        "src": "assets/videos/yellow-golf-source.mp4",
        "poster": "assets/posters/yellow-golf-source.jpg"
      },
      "ours": {
        "src": "assets/videos/yellow-golf-ours.mp4",
        "poster": "assets/posters/yellow-golf-ours.jpg"
      }
    }
  },
  {
    "id": "pink-boat",
    "videoId": "0058_boat",
    "editType": 3,
    "category": "color",
    "before": "White boat",
    "after": "Pink boat",
    "note": "Change the hull color while preserving the wake.",
    "width": 864,
    "height": 480,
    "duration": 4.688,
    "fps": "16/1",
    "frames": 75,
    "instruction": "Change the color of the boat from white to pink.",
    "sourcePrompt": "A white fishing boat is cruising steadily across the calm blue waters near a rocky shoreline with sparse vegetation and a few white buildings in the background. The camera remains fixed, capturing the boat's smooth movement and the gentle waves it creates.",
    "targetPrompt": "A pink fishing boat is cruising steadily across the calm blue waters near a rocky shoreline with sparse vegetation and a few white buildings in the background. The camera remains fixed, capturing the boat's smooth movement and the gentle waves it creates.",
    "media": {
      "source": {
        "src": "assets/videos/pink-boat-source.mp4",
        "poster": "assets/posters/pink-boat-source.jpg"
      },
      "ours": {
        "src": "assets/videos/pink-boat-ours.mp4",
        "poster": "assets/posters/pink-boat-ours.jpg"
      }
    }
  },
  {
    "id": "blue-duck",
    "videoId": "0071_mallard-water",
    "editType": 3,
    "category": "color",
    "before": "Mallard",
    "after": "Blue mallard",
    "note": "A precise color change on rippling water.",
    "width": 864,
    "height": 480,
    "duration": 5.0,
    "fps": "16/1",
    "frames": 80,
    "instruction": "Add 'blue' to describe the mallard duck.",
    "sourcePrompt": "A mallard duck is gliding smoothly across the surface of a calm pond, creating gentle ripples in the water. The camera remains fixed, capturing the duck's serene movement.",
    "targetPrompt": "A blue mallard duck is gliding smoothly across the surface of a calm pond, creating gentle ripples in the water. The camera remains fixed, capturing the duck's serene movement.",
    "media": {
      "source": {
        "src": "assets/videos/blue-duck-source.mp4",
        "poster": "assets/posters/blue-duck-source.jpg"
      },
      "ours": {
        "src": "assets/videos/blue-duck-ours.mp4",
        "poster": "assets/posters/blue-duck-ours.jpg"
      }
    }
  },
  {
    "id": "red-dress",
    "videoId": "0011_lucia",
    "editType": 3,
    "category": "color",
    "before": "Black dress",
    "after": "Red dress",
    "note": "Change the dress color while keeping the walk.",
    "width": 864,
    "height": 480,
    "duration": 4.375,
    "fps": "16/1",
    "frames": 70,
    "instruction": "Change the black dress to a red dress.",
    "sourcePrompt": "A woman in a black dress is walking along a paved path in a lush green park, with trees and a wooden bench in the background. The camera remains fixed, capturing her steady movement.",
    "targetPrompt": "A woman in a red dress is walking along a paved path in a lush green park, with trees and a wooden bench in the background. The camera remains fixed, capturing her steady movement.",
    "media": {
      "source": {
        "src": "assets/videos/red-dress-source.mp4",
        "poster": "assets/posters/red-dress-source.jpg"
      },
      "ours": {
        "src": "assets/videos/red-dress-ours.mp4",
        "poster": "assets/posters/red-dress-ours.jpg"
      }
    }
  },
  {
    "id": "wooden-bus",
    "videoId": "0079_A_bus",
    "editType": 4,
    "category": "material",
    "before": "Bus",
    "after": "Wooden bus",
    "note": "A material change through a rainy night.",
    "width": 832,
    "height": 480,
    "duration": 5.063,
    "fps": "16/1",
    "frames": 81,
    "instruction": "Replace the bus with a wooden bus.",
    "sourcePrompt": "A bus is driving steadily through a rainy city street, with wet pavement and glowing streetlights. The camera slowly follows the bus as it moves through the scene.",
    "targetPrompt": "A wooden bus is driving steadily through a rainy city street, with wet pavement and glowing streetlights. The camera slowly follows the bus as it moves through the scene.",
    "media": {
      "source": {
        "src": "assets/videos/wooden-bus-source.mp4",
        "poster": "assets/posters/wooden-bus-source.jpg"
      },
      "ours": {
        "src": "assets/videos/wooden-bus-ours.mp4",
        "poster": "assets/posters/wooden-bus-ours.jpg"
      }
    }
  },
  {
    "id": "carbon-drift",
    "videoId": "0059_drift-straight",
    "editType": 4,
    "category": "material",
    "before": "Red sports car",
    "after": "Carbon-fiber sports car",
    "note": "A material change through a fast drift.",
    "width": 864,
    "height": 480,
    "duration": 3.125,
    "fps": "16/1",
    "frames": 50,
    "instruction": "Add carbon fiber to the car's description.",
    "sourcePrompt": "A red sports car is drifting skillfully around a race track, leaving tire marks on the asphalt. The camera follows the car's movement quickly, capturing the dynamic motion and the surrounding race track environment.",
    "targetPrompt": "A carbon fiber red sports car is drifting skillfully around a race track, leaving tire marks on the asphalt. The camera follows the car's movement quickly, capturing the dynamic motion and the surrounding race track environment.",
    "media": {
      "source": {
        "src": "assets/videos/carbon-drift-source.mp4",
        "poster": "assets/posters/carbon-drift-source.jpg"
      },
      "ours": {
        "src": "assets/videos/carbon-drift-ours.mp4",
        "poster": "assets/posters/carbon-drift-ours.jpg"
      }
    }
  },
  {
    "id": "dog-sunglasses",
    "videoId": "0089_A_dog",
    "editType": 5,
    "category": "addition",
    "before": "Dog",
    "after": "Add sunglasses",
    "note": "Add a clear accessory without losing the pose.",
    "width": 832,
    "height": 480,
    "duration": 5.063,
    "fps": "16/1",
    "frames": 81,
    "instruction": "Add sunglasses to the dog.",
    "sourcePrompt": "A dog is wagging its tail excitedly while sitting on a sandy beach with waves crashing in the background. The camera remains fixed, focusing on the dog's joyful expression.",
    "targetPrompt": "A dog wearing sunglasses is wagging its tail excitedly while sitting on a sandy beach with waves crashing in the background. The camera remains fixed, focusing on the dog's joyful expression.",
    "media": {
      "source": {
        "src": "assets/videos/dog-sunglasses-source.mp4",
        "poster": "assets/posters/dog-sunglasses-source.jpg"
      },
      "ours": {
        "src": "assets/videos/dog-sunglasses-ours.mp4",
        "poster": "assets/posters/dog-sunglasses-ours.jpg"
      }
    }
  },
  {
    "id": "silver-jeep-turn",
    "videoId": "0015_car-shadow",
    "editType": 1,
    "category": "subject",
    "before": "Silver car",
    "after": "Silver jeep",
    "note": "A precise vehicle change at an urban intersection.",
    "width": 864,
    "height": 480,
    "duration": 2.5,
    "fps": "16/1",
    "frames": 40,
    "instruction": "Change the car to a jeep.",
    "sourcePrompt": "A silver car is making a left turn at an urban intersection, surrounded by modern buildings and a pedestrian walking on the sidewalk. The camera remains stationary, capturing the car's smooth maneuver.",
    "targetPrompt": "A silver jeep is making a left turn at an urban intersection, surrounded by modern buildings and a pedestrian walking on the sidewalk. The camera remains stationary, capturing the jeep's smooth maneuver.",
    "media": {
      "source": {
        "src": "assets/videos/silver-jeep-turn-source.mp4",
        "poster": "assets/posters/silver-jeep-turn-source.jpg"
      },
      "ours": {
        "src": "assets/videos/silver-jeep-turn-ours.mp4",
        "poster": "assets/posters/silver-jeep-turn-ours.jpg"
      }
    }
  },
  {
    "id": "purple-bicycle",
    "videoId": "0075_A_bicycle",
    "editType": 3,
    "category": "color",
    "before": "Bicycle",
    "after": "Purple bicycle",
    "note": "A local color edit through a steady street roll.",
    "width": 832,
    "height": 480,
    "duration": 5.063,
    "fps": "16/1",
    "frames": 81,
    "instruction": "Add purple color to the bicycle.",
    "sourcePrompt": "A bicycle is rolling steadily along a cobblestone street, with historic buildings and flower boxes lining the road. The camera remains fixed, capturing the bicycle's smooth motion.",
    "targetPrompt": "A purple bicycle is rolling steadily along a cobblestone street, with historic buildings and flower boxes lining the road. The camera remains fixed, capturing the bicycle's smooth motion.",
    "media": {
      "source": {
        "src": "assets/videos/purple-bicycle-source.mp4",
        "poster": "assets/posters/purple-bicycle-source.jpg"
      },
      "ours": {
        "src": "assets/videos/purple-bicycle-ours.mp4",
        "poster": "assets/posters/purple-bicycle-ours.jpg"
      }
    }
  },
  {
    "id": "bear-cap",
    "videoId": "0009_bear",
    "editType": 5,
    "category": "addition",
    "before": "Bear",
    "after": "Bear with cap",
    "note": "Add a small accessory while preserving the walk.",
    "width": 864,
    "height": 480,
    "duration": 5.125,
    "fps": "16/1",
    "frames": 82,
    "instruction": "Add a cap to the bear.",
    "sourcePrompt": "A large brown bear is walking slowly across a rocky terrain in a zoo enclosure, surrounded by stone walls and scattered greenery. The camera remains fixed, capturing the bear's deliberate movements.",
    "targetPrompt": "A large brown bear wearing a cap is walking slowly across a rocky terrain in a zoo enclosure, surrounded by stone walls and scattered greenery. The camera remains fixed, capturing the bear's deliberate movements.",
    "media": {
      "source": {
        "src": "assets/videos/bear-cap-source.mp4",
        "poster": "assets/posters/bear-cap-source.jpg"
      },
      "ours": {
        "src": "assets/videos/bear-cap-ours.mp4",
        "poster": "assets/posters/bear-cap-ours.jpg"
      }
    }
  },
  {
    "id": "woman-to-man",
    "videoId": "0011_lucia",
    "editType": 1,
    "category": "subject",
    "before": "Woman in black dress",
    "after": "Man in black suit",
    "note": "A full subject and outfit change along the same path.",
    "width": 864,
    "height": 480,
    "duration": 4.375,
    "fps": "16/1",
    "frames": 70,
    "instruction": "Change the woman into a man and change her black dress into a black suit.",
    "sourcePrompt": "A woman in a black dress is walking along a paved path in a lush green park, with trees and a wooden bench in the background. The camera remains fixed, capturing her steady movement.",
    "targetPrompt": "A man in a black suit is walking along a paved path in a lush green park, with trees and a wooden bench in the background. The camera remains fixed, capturing his steady movement.",
    "media": {
      "source": {
        "src": "assets/videos/woman-to-man-source.mp4",
        "poster": "assets/posters/woman-to-man-source.jpg"
      },
      "ours": {
        "src": "assets/videos/woman-to-man-ours.mp4",
        "poster": "assets/posters/woman-to-man-ours.jpg"
      }
    }
  },
  {
    "id": "hawk-blue-bird",
    "videoId": "0077_A_hawk",
    "editType": 1,
    "category": "subject",
    "before": "Hawk",
    "after": "Blue bird",
    "note": "A tracked aerial subject change over the canyon.",
    "width": 832,
    "height": 480,
    "duration": 5.063,
    "fps": "16/1",
    "frames": 81,
    "instruction": "Change the hawk into a blue bird.",
    "sourcePrompt": "A hawk is soaring majestically over a rocky canyon, with the sun casting long shadows on the ground. The camera quickly tilts upward to track the hawk's flight.",
    "targetPrompt": "A blue bird is soaring majestically over a rocky canyon, with the sun casting long shadows on the ground. The camera quickly tilts upward to track the bird's flight.",
    "media": {
      "source": {
        "src": "assets/videos/hawk-blue-bird-source.mp4",
        "poster": "assets/posters/hawk-blue-bird-source.jpg"
      },
      "ours": {
        "src": "assets/videos/hawk-blue-bird-ours.mp4",
        "poster": "assets/posters/hawk-blue-bird-ours.jpg"
      }
    }
  },
  {
    "id": "pink-suv",
    "videoId": "0069_car-turn",
    "editType": 3,
    "category": "color",
    "before": "Silver SUV",
    "after": "Pink SUV",
    "note": "A clean vehicle color change through the mountain turn.",
    "width": 864,
    "height": 480,
    "duration": 5.0,
    "fps": "16/1",
    "frames": 80,
    "instruction": "Change the color of the SUV from silver to pink.",
    "sourcePrompt": "A silver SUV is navigating a winding mountain road surrounded by lush green forests and towering mountains in the background. The camera remains stationary, capturing the car's smooth turn along the curve of the road.",
    "targetPrompt": "A pink SUV is navigating a winding mountain road surrounded by lush green forests and towering mountains in the background. The camera remains stationary, capturing the car's smooth turn along the curve of the road.",
    "media": {
      "source": {
        "src": "assets/videos/pink-suv-source.mp4",
        "poster": "assets/posters/pink-suv-source.jpg"
      },
      "ours": {
        "src": "assets/videos/pink-suv-ours.mp4",
        "poster": "assets/posters/pink-suv-ours.jpg"
      }
    }
  },
  {
    "id": "cow-horse",
    "videoId": "0034_cows",
    "editType": 1,
    "category": "subject",
    "before": "Cow",
    "after": "Horse",
    "note": "A rural subject change with the same steady walk.",
    "width": 864,
    "height": 480,
    "duration": 6.5,
    "fps": "16/1",
    "frames": 104,
    "instruction": "Change the cow into a horse.",
    "sourcePrompt": "A brown and white cow is walking along a dirt path in a grassy field. The camera remains stationary, capturing the cow's steady movement.",
    "targetPrompt": "A brown and white horse is walking along a dirt path in a grassy field. The camera remains stationary, capturing the horse's steady movement.",
    "media": {
      "source": {
        "src": "assets/videos/cow-horse-source.mp4",
        "poster": "assets/posters/cow-horse-source.jpg"
      },
      "ours": {
        "src": "assets/videos/cow-horse-ours.mp4",
        "poster": "assets/posters/cow-horse-ours.jpg"
      }
    }
  },
  {
    "id": "boat-kayak",
    "videoId": "0083_A_boat",
    "editType": 1,
    "category": "subject",
    "before": "Boat",
    "after": "Kayak",
    "note": "Change the vessel while preserving the calm river motion.",
    "width": 832,
    "height": 480,
    "duration": 5.063,
    "fps": "16/1",
    "frames": 81,
    "instruction": "Replace the boat with a kayak.",
    "sourcePrompt": "A boat is sailing smoothly across a calm river, with trees and a small dock in the background. The camera remains fixed, capturing the boat's serene motion.",
    "targetPrompt": "A kayak is sailing smoothly across a calm river, with trees and a small dock in the background. The camera remains fixed, capturing the kayak's serene motion.",
    "media": {
      "source": {
        "src": "assets/videos/boat-kayak-source.mp4",
        "poster": "assets/posters/boat-kayak-source.jpg"
      },
      "ours": {
        "src": "assets/videos/boat-kayak-ours.mp4",
        "poster": "assets/posters/boat-kayak-ours.jpg"
      }
    }
  },
  {
    "id": "roller-batman",
    "videoId": "0024_hockey",
    "editType": 1,
    "category": "creative",
    "before": "Rollerblader",
    "after": "Batman",
    "note": "A character transformation through the same skating action.",
    "width": 864,
    "height": 480,
    "duration": 4.688,
    "fps": "16/1",
    "frames": 75,
    "instruction": "Change the person to a batman.",
    "sourcePrompt": "A person on rollerblades is skillfully maneuvering a hockey stick to control a small ball on an outdoor court. The environment is an open area with a green fence and graffiti in the background. The camera remains stationary, capturing the dynamic movements of the person as they glide across the court.",
    "targetPrompt": "A batman on rollerblades is skillfully maneuvering a hockey stick to control a small ball on an outdoor court. The environment is an open area with a green fence and graffiti in the background. The camera remains stationary, capturing the dynamic movements of the batman as he glides across the court.",
    "media": {
      "source": {
        "src": "assets/videos/roller-batman-source.mp4",
        "poster": "assets/posters/roller-batman-source.jpg"
      },
      "ours": {
        "src": "assets/videos/roller-batman-ours.mp4",
        "poster": "assets/posters/roller-batman-ours.jpg"
      }
    }
  },
  {
    "id": "red-snowboarder",
    "videoId": "0037_snowboard-sand",
    "editType": 3,
    "category": "color",
    "before": "Snowboarder",
    "after": "Red snowboarder",
    "note": "A local outfit edit through a long sand descent.",
    "width": 864,
    "height": 480,
    "duration": 3.438,
    "fps": "16/1",
    "frames": 55,
    "instruction": "Change the woman's outfit to red.",
    "sourcePrompt": "A woman is snowboarding down a vast sand dune, maintaining her balance as she glides over the sandy surface. The camera follows her descent, capturing her dynamic movements and the expansive desert landscape. As she continues, she loses balance and falls onto the sand, creating a small cloud of dust around her.",
    "targetPrompt": "A woman in red is snowboarding down a vast sand dune, maintaining her balance as she glides over the sandy surface. The camera follows her descent, capturing her dynamic movements and the expansive desert landscape. As she continues, she loses balance and falls onto the sand, creating a small cloud of dust around her.",
    "media": {
      "source": {
        "src": "assets/videos/red-snowboarder-source.mp4",
        "poster": "assets/posters/red-snowboarder-source.jpg"
      },
      "ours": {
        "src": "assets/videos/red-snowboarder-ours.mp4",
        "poster": "assets/posters/red-snowboarder-ours.jpg"
      }
    }
  },
  {
    "id": "fighter-helicopter",
    "videoId": "0021_landing",
    "editType": 1,
    "category": "subject",
    "before": "Fighter jet",
    "after": "Helicopter",
    "note": "A tracked aircraft change on the carrier deck.",
    "width": 864,
    "height": 480,
    "duration": 2.188,
    "fps": "16/1",
    "frames": 35,
    "instruction": "Replace the fighter jet with a helicopter.",
    "sourcePrompt": "A fighter jet is landing on an aircraft carrier deck, with crew members in green and yellow vests observing the process. The camera remains stationary, capturing the jet's approach and landing.",
    "targetPrompt": "A helicopter is landing on an aircraft carrier deck, with crew members in green and yellow vests observing the process. The camera remains stationary, capturing the helicopter's approach and landing.",
    "media": {
      "source": {
        "src": "assets/videos/fighter-helicopter-source.mp4",
        "poster": "assets/posters/fighter-helicopter-source.jpg"
      },
      "ours": {
        "src": "assets/videos/fighter-helicopter-ours.mp4",
        "poster": "assets/posters/fighter-helicopter-ours.jpg"
      }
    }
  }
];
