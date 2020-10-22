#include <stdio.h>
#include <stdlib.h>

void rop(FILE *f)
{
	char buf[24];
	long i, fsize, read_size;

	puts("How many bytes do you want to read? (max: 24)");
	scanf("%ld", &i); // can be negative
	
	if (i > 24) {
		puts("You can't trick me...");
		return;
	}

	fseek(f, 0, SEEK_END); // pointer at end of file
	fsize = ftell(f); // finding file size
	fseek(f, 0, SEEK_SET); // going back to start

	read_size = (size_t) i < (size_t) fsize ? i : fsize; 
	fread(buf, 1, read_size, f);
	fclose(f);

	puts(buf);
}

int main(void)
{
	FILE *f = fopen("./exploit", "r");
	setbuf(f, 0);
	if (!f)
		puts("Error opening ./exploit");
	else
		rop(f);
	return 0;
}
