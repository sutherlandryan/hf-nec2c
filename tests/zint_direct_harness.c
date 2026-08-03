/* SPDX-License-Identifier: BSD-2-Clause */

#include <complex.h>
#include <math.h>
#include <stdio.h>

#include "nec2c.h"

typedef struct
{
	double target_x;
	const char *expected_branch;
} zint_case_t;

int main( int argc, char **argv )
{
	static const zint_case_t cases[] = {
		{ 0.1, "small" },
		{ 1.0, "small" },
		{ 2.97, "small" },
		{ 7.999, "small" },
		{ 8.0, "small" },
		{ 8.001, "medium" },
		{ 20.0, "medium" },
		{ 50.0, "medium" },
		{ 109.999, "medium" },
		{ 110.0, "medium" },
		{ 110.001, "large" },
		{ 200.0, "large" }
	};
	const double sigl = 1.0;
	const double tpcmu = 2.368705e+3;
	size_t index;

	(void)argc;
	(void)argv;
	puts( "target_x\tactual_x\tbranch\treal\timag" );

	for( index = 0; index < sizeof( cases ) / sizeof( cases[0] ); index++ )
	{
		double rolam = cases[index].target_x / sqrt( tpcmu* sigl );
		double actual_x = sqrt( tpcmu* sigl )* rolam;
		const char *branch = actual_x <= 8.0 ? "small" :
			(actual_x <= 110.0 ? "medium" : "large");
		complex double value;

		zint( sigl, rolam, &value );
		if( branch[0] != cases[index].expected_branch[0] )
			return( 2 );

		printf( "%a\t%a\t%s\t%a\t%a\n",
			cases[index].target_x,
			actual_x,
			branch,
			creal( value ),
			cimag( value ) );
	}

	return( 0 );
}
