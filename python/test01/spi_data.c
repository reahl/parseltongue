/*do other stuff
*
*/
//#include <Python.h>

extern double max_value(double dataIn[], int size){
	double max_val = dataIn[0];
	for(int i=0; i<size; i++){
		if(max_val < dataIn[i])
			max_val = dataIn[i];
	}
	return max_val;
}