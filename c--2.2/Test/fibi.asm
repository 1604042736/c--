global _main
extern _printf

section .text:
f:
push ebp
mov ebp,esp
sub esp,4
mov ecx,ebp
add ecx,8
mov eax,[ecx]
push eax
push 1
pop edx
push edx
pop ebx
pop eax
cmp eax,ebx
jne _4
push 1
jmp _5
_4:
push 0
_5:
pop eax
cmp eax,0
je _3
push 1
jmp _2
_3:
push 0
_2:
mov ecx,ebp
add ecx,8
mov eax,[ecx]
push eax
push 2
pop edx
push edx
pop ebx
pop eax
cmp eax,ebx
jne _8
push 1
jmp _9
_8:
push 0
_9:
pop eax
cmp eax,0
je _7
push 1
jmp _6
_7:
push 0
_6:
pop ebx
pop eax
cmp eax,0
jne _10
cmp ebx,0
je _11
_10:
push 1
jmp _12
_11:
push 0
_12:
pop eax
cmp eax,0
je _1
push 1
jmp _0
_1:
push 0
_0:
pop eax
cmp eax,0
je _13
push 1
pop eax
mov esp,ebp
pop ebp
ret 
jmp _14
_13:
_14:
mov ecx,ebp
add ecx,8
mov eax,[ecx]
push eax
push 1
pop ebx
pop eax
sub eax,ebx
push eax
call f
add esp,4
push eax
mov ecx,ebp
add ecx,8
mov eax,[ecx]
push eax
push 2
pop ebx
pop eax
sub eax,ebx
push eax
call f
add esp,4
push eax
pop ebx
pop eax
add eax,ebx
push eax
pop eax
mov esp,ebp
pop ebp
ret 
mov esp,ebp
pop ebp
ret 
_main:
push ebp
mov ebp,esp
sub esp,0
push 10
call f
add esp,4
push eax
push constant0
call _printf
add esp,4
mov esp,ebp
pop ebp
ret 
section .data:
constant0 db '%d'