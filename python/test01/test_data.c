/*More functions to test.
*
*/
#include <stdio.h>
#include <stdlib.h> 
#include "test_data.h"

double max_value(double *p, int input_size){
	double max_val = *p;
	for(int i=1; i<input_size; i++){
		if(max_val < *(p + i))
			max_val = *(p + i);
	}
	return max_val;
}

double * test_data(double *input_data, int new_size, int option){

	static int old_size = 0;
	static double *data = NULL;
	if(option == 1){
		if (!old_size){
			old_size = new_size;
			data = calloc(old_size,sizeof(double));
		}
		if (new_size==old_size)
			for (int i=0;i<old_size;i++)
				data[i] = input_data[i];
	}
	else if(option == 3){
		free(data);
		data = NULL;
		old_size = 0;
	}

	return data;
}