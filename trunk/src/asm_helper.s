	.text
	.globl serialize_helper
serialize_helper:	
	pushl %ebp
	pushl %ebx
	movl $0, %eax
	cpuid
	popl %ebx
	popl %ebp
	ret
