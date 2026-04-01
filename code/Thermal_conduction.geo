cm = 1;
lc = 0.06*cm;
//1
Pipe_P = 1.6*Sqrt(3) * cm ;
Pipe_D = 1.575 * cm ;
Pipe_r = 1.575/2 * cm ;
//2
Fuel_P = 1.6 * cm ;
Fuel_D = 1.425 * cm ;
Fuel_r = 1.425/2 * cm ;
//Rod_r = 8.85 * cm ;
//3
Rod_R = 8.84 *cm;
Rod_r = Rod_R+0.01 * cm ;
Ref_r = 55.625 * cm ;

// 
Macro CircleHolehole
	//Inner HeatPipe Circle
	p1 = newp; Point(p1) = {x+Pitch/2,               y+Pitch/2,              0, lc};  // center
	p2 = newp; Point(p2) = {x+Pitch/2,               y+Pitch/2 - Radius,  0, lc}; // bottom
	p3 = newp; Point(p3) = {x+Pitch/2 + Radius, y+Pitch/2,               0, lc}; // right
	p4 = newp; Point(p4) = {x+Pitch/2,               y+Pitch/2 + Radius, 0, lc}; // top
	p5 = newp; Point(p5) = {x+Pitch/2 - Radius,  y+Pitch/2,               0, lc}; // left

	c1 = newreg; Circle(c1) = {p2, p1, p3};
	c2 = newreg; Circle(c2) = {p3, p1, p4};
	c3 = newreg; Circle(c3) = {p4, p1, p5};
	c4 = newreg; Circle(c4) = {p5, p1, p2};

        l = newreg;
        Physical Curve(l) = {c1, c2, c3, c4};
        ll = newreg; Curve Loop(ll) = {c1, c2, c3, c4};
        
	//pin = newreg;
	//theloops[pin] = ll;
Return

Macro CircleHolesurface
	//Inner HeatPipe Circle
	p1 = newp; Point(p1) = {x+Pitch/2,               y+Pitch/2,              0, lc};  // center
	p2 = newp; Point(p2) = {x+Pitch/2,               y+Pitch/2 - Radius,  0, lc}; // bottom
	p3 = newp; Point(p3) = {x+Pitch/2 + Radius, y+Pitch/2,               0, lc}; // right
	p4 = newp; Point(p4) = {x+Pitch/2,               y+Pitch/2 + Radius, 0, lc}; // top
	p5 = newp; Point(p5) = {x+Pitch/2 - Radius,  y+Pitch/2,               0, lc}; // left

	c1 = newreg; Circle(c1) = {p2, p1, p3};
	c2 = newreg; Circle(c2) = {p3, p1, p4};
	c3 = newreg; Circle(c3) = {p4, p1, p5};
	c4 = newreg; Circle(c4) = {p5, p1, p2};
	l = newreg;
	Physical Curve(l) = {c1, c2, c3, c4};
	ll = newreg; Curve Loop(ll) = {c1, c2, c3, c4};
	
    Plane Surface(ll) = {ll};
	Physical Surface(ll) = {ll};

    

        
	//pin = newreg;
	//theloops[pin] = ll;
Return
//
//Macro HeatpipeHole
	//Inner HeatPipe Circle
//	p1 = newp; Point(p1) = {x+Pitch/2,               y+Pitch/2,              0, lc};  // center
//	p2 = newp; Point(p2) = {x+Pitch/2,               y+Pitch/2 - Radius,  0, lc}; // bottom
//	p3 = newp; Point(p3) = {x+Pitch/2 + Radius, y+Pitch/2,               0, lc}; // right
//	p4 = newp; Point(p4) = {x+Pitch/2,               y+Pitch/2 + Radius, 0, lc}; // top
//	p5 = newp; Point(p5) = {x+Pitch/2 - Radius,  y+Pitch/2,               0, lc}; // left

//	c1 = newreg; Circle(c1) = {p2, p1, p3};
//	c2 = newreg; Circle(c2) = {p3, p1, p4};
//	c3 = newreg; Circle(c3) = {p4, p1, p5};
//	c4 = newreg; Circle(c4) = {p5, p1, p2};

        //l = newreg;
        //Physical Curve("heatpipe",l) = {c1, c2, c3, c4};
//        ll = newreg; Curve Loop(ll) = {c1, c2, c3, c4};
//	pin = newreg;
//	theloops[pin] = ll;
//Return


//heatpipe
Pitch = Pipe_P ;
Radius = Pipe_r ;
x = Rod_r-Pipe_P/2+ Pipe_r;
y = -(2*Pitch) ; 
For i In {4:12}
	For j In {0:i-1}
		Call CircleHolehole;
		y += Pitch;
                //Physical Curve("heatpipe") += ll; 
	EndFor
	y = y - Pitch*i-Pitch/2;
	x += Pitch/2*Sqrt(3);
EndFor	

//fuel 1
Pitch = Fuel_P ;
Radius = Fuel_r ;
x = (Rod_r-Pipe_P/2+ Pipe_r)+Pipe_P/2;
y = -(2*Pipe_P)+Pipe_P/2 +Sqrt(3)*Fuel_P/2 -Fuel_P/2; 
For i In {3:10}
	For j In {0:i-1}
		Call CircleHolesurface;
		y += Sqrt(3)*Pitch;
	EndFor
	y = y - Sqrt(3)*Pitch*i-Sqrt(3)*Pitch/2;
	x += 1.5*Pitch;
EndFor

//fuel 2
Pitch = Fuel_P ;
Radius = Fuel_r ;
x = (Rod_r-Pipe_P/2+ Pipe_r)+Pipe_P/2+Fuel_P/2;
y = -(2*Pipe_P)+Pipe_P/2-Fuel_P/2; 
For i In {4:11}
	For j In {0:i-1}
		Call CircleHolesurface;
		y += Sqrt(3)*Pitch;
	EndFor
	y = y - Sqrt(3)*Pitch*i-Sqrt(3)*Pitch/2;
	x += 1.5*Pitch;
EndFor

//others
//+
Point(921) = {0, 0, 0, 1.0};

Point(922) = {Rod_R-1, (Rod_R-1)/Sqrt(3), 0, 1.0};
Point(923) = {Rod_R-1, -(Rod_R-1)/Sqrt(3), 0, 1.0};
//4
Block_x = 29.625 *cm;
Point(924) = {Block_x+1, (Block_x+1)/Sqrt(3), 0, 1.0};
Point(925) = {Block_x+1, -(Block_x+1)/Sqrt(3), 0, 1.0};

Point(926) = {Ref_r, Ref_r/Sqrt(3), 0, 1.0};
Point(927) = {Ref_r, -Ref_r/Sqrt(3), 0, 1.0};

// block
Line(3337) = {922, 923};
Line(3338) = {922, 924};
Line(3339) = {923, 925};
Line(3340) = {925, 924};
//+
Curve Loop(3340) = {3340, -3338, 3337, 3339};
//+
//Physical Surface("heatpipe", 3341) = {6};
//For i In {12:1224:6}
//        Physical Surface("heatpipe", 3341) += {i};
//EndFor
//+
//For i In {2238:3336:6}
//	Physical Surface(i) = {i};
//EndFor
//+
//+
//6 * (1-112, 113-184)
Plane Surface(1) = {6, 12, 18, 24, 30, 36, 42, 48, 54, 60, 66, 72, 78, 84, 90, 96, 102, 108, 114, 120, 126, 132, 138, 144, 150, 156, 162, 168, 174, 180, 186, 192, 198, 204, 210, 216, 222, 228, 234, 240, 246, 252, 258, 264, 270, 276, 282, 288, 294, 300, 306, 312, 318, 324, 330, 336, 342, 348, 354, 360, 366, 372, 378, 384, 390, 396, 402, 408, 414, 420, 426, 432, 438, 444, 450, 456, 462, 468, 474, 480, 486, 492, 498, 504, 510, 516, 522, 528, 534, 540, 546, 552, 558, 564, 570, 576, 582, 588, 594, 600, 606, 612, 618, 624, 630, 636, 642, 648, 654, 660, 666, 672, 678, 684, 690, 696, 702, 708, 714, 720, 726, 732, 738, 744, 750, 756, 762, 768, 774, 780, 786, 792, 798, 804, 810, 816, 822, 828, 834, 840, 846, 852, 858, 864, 870, 876, 882, 888, 894, 900, 906, 912, 918, 924, 930, 936, 942, 948, 954, 960, 966, 972, 978, 984, 990, 996, 1002, 1008, 1014, 1020, 1026, 1032, 1038, 1044, 1050, 1056, 1062, 1068, 1074, 1080, 1086, 1092, 1098, 1104, 3340};
//+
Physical Surface(4001) = {1};
//+
Physical Curve(3341) = {3338};
//+
Physical Curve(3342) = {3340};
//+
Physical Curve(3343) = {3339};
//+
Physical Curve(3344) = {3337};
